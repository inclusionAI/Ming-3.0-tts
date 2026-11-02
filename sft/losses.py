# Copyright (c) Ant Group. All rights reserved.
"""Native TTS objectives, normalized by valid elements across all ranks."""
import torch
import torch.distributed as dist
import torch.nn.functional as F


def global_means(sums, counts):
    """Account for DDP's gradient averaging when ranks have unequal lengths."""
    stats = torch.stack([torch.as_tensor(c, device=sums[0].device, dtype=torch.float32)
                         for c in counts] + [s.detach().float() for s in sums])
    world = 1
    if dist.is_available() and dist.is_initialized():
        dist.all_reduce(stats)
        world = dist.get_world_size()
    n = len(sums)
    result = []
    for local, count, total in zip(sums, stats[:n], stats[n:]):
        backward = local * world / count.clamp_min(1)
        result.append((backward + total / count.clamp_min(1) - backward.detach())
                      * (count > 0))
    return result


def stop_statistics(logits, labels):
    """One positive and the hardest eligible negative per utterance."""
    positive = torch.full_like(labels, -100)
    negative = torch.full_like(labels, -100)
    positive[labels == 1] = 1
    eligible = labels == 0
    scores = logits.detach().float().softmax(-1)[..., 0].masked_fill(~eligible, float('inf'))
    rows = torch.nonzero(eligible.any(-1), as_tuple=True)[0]
    if rows.numel():
        negative[rows, scores[rows].argmin(-1)] = 0
    flat = logits.float().reshape(-1, 2)
    return (F.cross_entropy(flat, positive.reshape(-1), ignore_index=-100, reduction='sum'),
            positive.ne(-100).sum(),
            F.cross_entropy(flat, negative.reshape(-1), ignore_index=-100, reduction='sum'),
            negative.ne(-100).sum())
