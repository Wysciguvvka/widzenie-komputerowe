import numpy as np


def func(prev_frame, next_frame, _):
    prev_frame_normalized = prev_frame.astype(np.float32) / 255.0
    next_frame_normalized = next_frame.astype(np.float32) / 255.0

    interpolated_frame_normalized = 0.5 * (prev_frame_normalized + next_frame_normalized)

    interpolated_frame = np.clip(interpolated_frame_normalized * 255.0, 0, 255).astype(np.uint8)

    return interpolated_frame
