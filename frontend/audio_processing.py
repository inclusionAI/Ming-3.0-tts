"""Waveform postprocessing shared by the dense and Tiny inference APIs."""

# Trailing-silence trim, matching the reference implementation's defaults.
SILENCE_FRAME_SECONDS = 0.1
SILENCE_THRESHOLD = 1e-3
SILENCE_TAIL_SECONDS = 0.3


def trim_trailing_silence(
    speech,
    sample_rate,
    threshold=SILENCE_THRESHOLD,
    tail_seconds=SILENCE_TAIL_SECONDS,
):
    """Cut the trailing silence, keeping a fixed tail.

    The model keeps emitting near-silent frames after the utterance ends, and
    how many it emits varies per fragment. This is the non-streaming
    equivalent of the reference implementation's silence holder: scan 0.1 s
    frames backwards for the last one above ``threshold`` and keep
    ``tail_seconds`` beyond it.
    """
    if speech.numel() == 0:
        return speech

    frame = int(sample_rate * SILENCE_FRAME_SECONDS)
    tail = int(sample_rate * tail_seconds)
    if frame <= 0 or speech.shape[-1] < frame:
        return speech[..., :tail]

    # Drop the sub-frame remainder, as the reference does before unfolding.
    num_frames = (speech.shape[-1] - frame) // frame + 1
    speech = speech[..., :num_frames * frame]

    scores = speech.unfold(-1, frame, frame).abs().mean(dim=-1)
    scores = scores.mean(dim=list(range(scores.dim() - 1)))

    index = int(scores.shape[0]) - 1
    while index >= 0 and scores[index] <= threshold:
        index -= 1
    if index < 0:
        # Silent throughout; emit the fixed tail rather than nothing.
        return speech[..., :tail]
    return speech[..., :index * frame + frame + tail]
