import numpy as np
from scipy.interpolate import RectBivariateSpline

def func(prev_frame, next_frame, optical_flow, t=0.5, kx=3, ky=3, s=0):
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
        # Use RectBivariateSpline for interpolation
        spline1 = RectBivariateSpline(np.arange(height), np.arange(width),
                                       prev_frame[..., c], kx=kx, ky=ky, s=s)
        spline2 = RectBivariateSpline(np.arange(height), np.arange(width),
                                       next_frame[..., c], kx=kx, ky=ky, s=s)

        # Evaluate the splines at the specified points
        interpolated_frame[..., c] = (
                t * spline1(yt1, xt1, grid=False) +
                (1 - t) * spline2(yt2, xt2, grid=False)
        )

    interpolated_frame = np.clip(interpolated_frame, 0, 255).astype(np.uint8)
    return interpolated_frame