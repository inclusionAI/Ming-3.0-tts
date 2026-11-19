"""CUDA-graph replay of the 0.5b sampler, with bit-identical output.

Per audio frame, ``BailingMMNativeForConditionalGeneration.sample`` runs the
flow head (10 DiT passes with CFG), the stop head, the audio aggregator and
the 24 LLM layers. At batch 1 these are thousands of small kernels, and most
of the frame time goes to launching them from Python, not to the maths. This
module records that per-frame work once in CUDA graphs and replays it.

The output is the same, sample for sample, as the eager sampler:

- the same modules run the same ops on the same shapes, so the same kernels run;
- the per-frame noise is drawn eagerly, in the original order, shape and dtype,
  so a seeded run consumes the RNG exactly as before;
- the KV cache lives in fixed buffers, and attention reads it through
  ``repeat_kv``, which copies it to a contiguous tensor as before;
- the attention mask is built eagerly per KV length, as ``Qwen2Model`` does.

The LLM graphs are keyed by KV length (at most ``MAX_CACHE_LEN``), the flow
graph by ``(cfg, sigma, temperature)``. Both are kept for the life of the
process, so each new ``(cfg, sigma, temperature)`` adds one graph. Graphs
record parameter addresses: move or recast the model before enabling them,
not after. One request runs at a time per model; a concurrent request raises.
Call it through ``generate()``/``MingTTS.synthesize``, which set the bfloat16
autocast the graphs were recorded under.

Anything outside the supported configuration (dense LLM, batch 1,
``patch_size == history_patch_size == 1``, the model on the current CUDA
device, transformers 4.x) keeps the eager sampler with a warning.

Usage::

    tts = MingTTS(model_path, cuda_graphs=True)
"""
from __future__ import annotations

import threading
import types
import warnings

import torch
import transformers
from transformers.cache_utils import Cache

from modeling_bailingmm import MAX_CACHE_LEN


class _SlotCache(Cache):
    """KV cache in fixed buffers; ``length`` is the KV length after this step."""

    def __init__(self, keys, values):
        super().__init__()
        self.keys, self.values, self.length = keys, values, 0

    def update(self, key_states, value_states, layer_idx, cache_kwargs=None):
        end = self.length
        start = end - key_states.shape[-2]
        self.keys[layer_idx][:, :, start:end].copy_(key_states)
        self.values[layer_idx][:, :, start:end].copy_(value_states)
        return self.keys[layer_idx][:, :, :end], self.values[layer_idx][:, :, :end]

    def get_seq_length(self, layer_idx=0):
        return self.length - 1


class GraphedSampler:
    def __init__(self, model):
        self.model = model
        llm = model.model.model  # Qwen2Model
        cfg = llm.config
        device = model.device
        dtype = torch.bfloat16
        head_dim = cfg.hidden_size // cfg.num_attention_heads
        shape = (1, cfg.num_key_value_heads, MAX_CACHE_LEN, head_dim)
        self.cache = _SlotCache(
            [torch.zeros(shape, device=device, dtype=dtype) for _ in llm.layers],
            [torch.zeros(shape, device=device, dtype=dtype) for _ in llm.layers],
        )
        self.latent_in = torch.zeros(1, 1, model.latent_dim, device=device, dtype=dtype)
        self.position = torch.zeros(1, 1, device=device, dtype=torch.long)
        self.noise = torch.zeros(1, 1, model.latent_dim, device=device, dtype=dtype)
        self.sde_noise = torch.zeros(10, 1, 1, model.latent_dim, device=device, dtype=dtype)
        self.cond = torch.zeros(1, 1, cfg.hidden_size, device=device, dtype=dtype)
        self.history = torch.zeros(1, model.history_patch_size, model.latent_dim, device=device, dtype=dtype)
        self.pool = torch.cuda.graph_pool_handle()
        self.stream = torch.cuda.Stream()
        self.busy = threading.Lock()
        self.warmed = set()
        self.decode_graphs = {}  # kv length -> (graph, hidden output)
        self.flow_graphs = {}    # (cfg, sigma, temperature) -> (graph, latent output)

    # -- capture ----------------------------------------------------------
    def _capture(self, fn):
        # The first capture of each kind runs once eagerly, so lazy cuBLAS and
        # workspace setup does not happen during capture. The raw capture API
        # skips the gc.collect() and empty_cache() that torch.cuda.graph runs
        # on every capture, which would dominate capturing every KV length.
        current = torch.cuda.current_stream()
        self.stream.wait_stream(current)
        with torch.cuda.stream(self.stream), \
                torch.autocast("cuda", dtype=torch.bfloat16, cache_enabled=False):
            if fn.__name__ not in self.warmed:
                fn()
                self.warmed.add(fn.__name__)
                torch.cuda.synchronize()
            graph = torch.cuda.CUDAGraph()
            # Thread-local, so CUDA work from other threads during a lazy
            # capture does not invalidate it.
            graph.capture_begin(pool=self.pool, capture_error_mode="thread_local")
            try:
                out = fn()
            finally:
                graph.capture_end()
        current.wait_stream(self.stream)
        return graph, out

    @torch.inference_mode()
    def warm(self, cfg=2.0, sigma=0.25, temperature=0.0, min_length=32):
        """Capture every graph a request could need, so none is captured mid-request."""
        self._flow_graph(cfg, sigma, temperature)
        for length in range(min_length, MAX_CACHE_LEN + 1):
            self._decode_graph(length)
        torch.cuda.synchronize()

    def _decode_graph(self, length):
        entry = self.decode_graphs.get(length)
        if entry is None:
            llm = self.model.model.model
            self.cache.length = length
            # What Qwen2Model.forward computes for a decode step: a (1, 1)
            # mask of ones and ``length - 1`` cached tokens.
            mask = llm._update_causal_mask(
                torch.ones(1, 1, device=self.position.device),
                self.cond,
                torch.arange(length - 1, length, device=self.position.device),
                self.cache,
                False,
            )

            def decode_step():
                self.cache.length = length
                hidden = self.model.linear_proj_audio(self.latent_in)
                embeddings = llm.rotary_emb(hidden, self.position)
                for layer in llm.layers:
                    hidden = layer(
                        hidden, attention_mask=mask, position_ids=self.position,
                        past_key_value=self.cache, output_attentions=False,
                        use_cache=True, cache_position=None,
                        position_embeddings=embeddings,
                    )[0]
                return llm.norm(hidden)

            entry = self.decode_graphs[length] = self._capture(decode_step)
        return entry

    def _flow_graph(self, cfg, sigma, temperature):
        key = (cfg, sigma, temperature)
        entry = self.flow_graphs.get(key)
        if entry is None:
            cfm = self.model.flowloss.cfm

            def flow_step():
                return cfm.sample(
                    noise=self.noise, c=self.cond, latent_history=self.history,
                    sde_noise=self.sde_noise, cfg_scale=cfg, patch_size=1,
                    sigma=sigma, temperature=temperature,
                )

            entry = self.flow_graphs[key] = self._capture(flow_step)
        return entry

    # -- sampling -----------------------------------------------------------
    def sample(self, *args, **kwargs):
        # The KV cache and the step buffers are shared, so a second request on
        # the same model would silently corrupt the first one.
        if not self.busy.acquire(blocking=False):
            raise RuntimeError("CUDA-graph sampling runs one request at a time per model")
        try:
            yield from self._sample(*args, **kwargs)
        finally:
            self.busy.release()

    def _sample(self, prompt, text, spk_emb=None, instruction=None,
                prompt_waveform=None, prompt_text=None, max_decode_steps=1000,
                cfg=2.0, sigma=0.25, temperature=0, use_zero_spk_emb=False,
                prompt_latent=None):
        model = self.model
        if prompt_text is None:
            prompt_latent = None
        elif prompt_latent is None and prompt_waveform is not None:
            prompt_latent = model.encode_prompt_latent(prompt_waveform)

        _, inputs_embeds = model.prepare_input_embed(
            prompt=prompt, text=text, spk_emb=spk_emb, instruction=instruction,
            prompt_latent=prompt_latent, prompt_text=prompt_text,
            use_zero_spk_emb=use_zero_spk_emb,
        )
        prompt_length = inputs_embeds.shape[1]
        attention_mask = torch.ones((1, prompt_length), device=inputs_embeds.device)
        position_ids = (attention_mask.cumsum(-1) - 1).masked_fill_((attention_mask == 0), 1)

        # The prefill runs once per request, so it stays eager.
        with torch.autocast(device_type="cuda", dtype=torch.bfloat16):
            outputs = model.model(
                attention_mask=attention_mask, position_ids=position_ids,
                inputs_embeds=inputs_embeds, audio_mask=None, image_mask=None,
                output_hidden_states=True, return_dict=True, use_cache=True,
                past_key_values=None,
            )
        for layer, (key, value) in enumerate(outputs.past_key_values):
            self.cache.keys[layer][:, :, :prompt_length].copy_(key)
            self.cache.values[layer][:, :, :prompt_length].copy_(value)
        # ``cond`` holds the current hidden state for the whole step. Graph
        # outputs live in the shared pool, where a later replay of another
        # graph may reuse their memory, so they are copied out at once.
        z = self.cond
        z.copy_(outputs.hidden_states[-1][:, -1:, :])
        del outputs

        self.history.zero_()
        if prompt_latent is not None:
            prompt_latent = prompt_latent.to(z.dtype)
            start = model.history_patch_size - prompt_latent.size(1)
            if start < 0:
                self.history[:] = prompt_latent[:, -start:, :]
            else:
                self.history[:, start:, :] = prompt_latent

        flow, flow_out = self._flow_graph(cfg, sigma, temperature)
        budget = (MAX_CACHE_LEN - prompt_length) // model.patch_size
        position = prompt_length - 1
        for step in range(min(max_decode_steps, budget)):
            # The same draws, order, shape and dtype as FlowLoss.sample.
            noise = torch.randn((1, 1, model.flowloss.z_channels), device=z.device, dtype=z.dtype)
            sde_noise = torch.randn((10, *noise.shape), device=z.device, dtype=z.dtype)
            self.noise.copy_(noise)
            self.sde_noise.copy_(sde_noise)
            flow.replay()
            latent = flow_out.clone()

            if model.stop_head(z)[0][0].softmax(dim=-1)[1] > 0.5 and step > 3:
                yield latent, True
                return
            yield latent, False

            position += 1
            self.position.fill_(position)
            self.latent_in.copy_(latent)
            self.history[:, -1:, :] = latent
            graph, hidden = self._decode_graph(position + 1)
            graph.replay()
            z.copy_(hidden)


def enable_cuda_graphs(model, warm=True, cfg=2.0, sigma=0.25, temperature=0.0):
    """Replace ``model.sample`` with CUDA-graph replay. Returns True if enabled.

    ``warm`` captures every graph up front (one flow graph for the given
    ``cfg``/``sigma``/``temperature`` and one LLM graph per KV length), so the
    first request is as fast as later ones. Other ``cfg``/``sigma``/
    ``temperature`` values are captured on first use.
    """
    device = model.device
    problems = [
        message for failed, message in (
            (model.model_type != "dense", "the LLM is not dense"),
            (model.patch_size != 1 or model.history_patch_size != 1, "patch_size or history_patch_size is not 1"),
            (device.type != "cuda", f"the model is on {device}, not CUDA"),
            (device.type == "cuda" and (device.index or 0) != torch.cuda.current_device(),
             f"the model is on {device}, not the current CUDA device"),
            (int(transformers.__version__.split(".")[0]) != 4,
             f"transformers {transformers.__version__} is not 4.x"),
        ) if failed
    ]
    if problems:
        warnings.warn("CUDA graphs not enabled, using the eager sampler: " + "; ".join(problems))
        return False
    sampler = GraphedSampler(model)
    model.sample = types.MethodType(lambda self, *a, **k: sampler.sample(*a, **k), model)
    if warm:
        sampler.warm(cfg=cfg, sigma=sigma, temperature=temperature)
    return True
