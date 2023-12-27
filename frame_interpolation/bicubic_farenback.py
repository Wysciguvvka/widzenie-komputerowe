import cv2
import numpy as np


def func(prev_frame, next_frame, optical_flow, alpha=0.8):
    h, w = next_frame.shape[:2]
    scaled_optical_flow = alpha * optical_flow
    y, x = np.mgrid[0:h, 0:w]
    flow_map = np.column_stack((x.flatten(), y.flatten())) + scaled_optical_flow.reshape(-1, 2)
    flow_map[:, 0] = np.clip(flow_map[:, 0], 0, w - 1)
    flow_map[:, 1] = np.clip(flow_map[:, 1], 0, h - 1)
    flow_map = flow_map.reshape(h, w, 2).astype(np.float32)
    interpolated_frame = cv2.remap(prev_frame, flow_map[:, :, 0], flow_map[:, :, 1], interpolation=cv2.INTER_LINEAR)
    return interpolated_frame

