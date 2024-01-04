import numpy as np
import cv2


def func(prev_frame, next_frame, optical_flow, t=0.5):
    height, width, channels = prev_frame.shape
    flow_x, flow_y = optical_flow[:, :, 0], optical_flow[:, :, 1]
    x_grid, y_grid = np.meshgrid(np.arange(width), np.arange(height))

    interp_x1 = x_grid - t * flow_x
    interp_y1 = y_grid - t * flow_y
    xt1 = np.maximum(np.minimum(interp_x1, width - 1), 0).astype(int)
    yt1 = np.maximum(np.minimum(interp_y1, height - 1), 0).astype(int)

    interp_x2 = x_grid + (1 - t) * flow_x
    interp_y2 = y_grid + (1 - t) * flow_y
    xt2 = np.maximum(np.minimum(interp_x2, width - 1), 0).astype(int)
    yt2 = np.maximum(np.minimum(interp_y2, height - 1), 0).astype(int)

    interpolated_frame = np.zeros_like(prev_frame, dtype=np.float32)

    for c in range(channels):
        interpolated_frame[..., c] = (
                t * cv2.remap(prev_frame[..., c], xt1.astype(np.float32), yt1.astype(np.float32),
                              interpolation=cv2.INTER_CUBIC) +
                (1 - t) * cv2.remap(next_frame[..., c], xt2.astype(np.float32), yt2.astype(np.float32),
                                    interpolation=cv2.INTER_CUBIC)
        )

    interpolated_frame = np.clip(interpolated_frame, 0, 255).astype(np.uint8)
    return interpolated_frame


func.__name__ = "Interpolacja kubiczna"
