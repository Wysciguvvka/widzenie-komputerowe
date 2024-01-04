import cv2
import numpy as np


def func(prev_frame: np.ndarray, next_frame: np.ndarray, *, debug=False):
    prev_frame_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
    next_frame_gray = cv2.cvtColor(next_frame, cv2.COLOR_BGR2GRAY)
    prev_frame_gray = cv2.GaussianBlur(prev_frame_gray, (5, 5), 0)
    next_frame_gray = cv2.GaussianBlur(next_frame_gray, (5, 5), 0)
    optical_flow = cv2.calcOpticalFlowFarneback(prev_frame_gray, next_frame_gray, None,  # noqa
                                                pyr_scale=0.5, levels=3, winsize=200,
                                                iterations=4, poly_n=2, poly_sigma=1.1, flags=0)

    flow_img = next_frame.copy()
    h, w = flow_img.shape[:2]
    step_size = 60
    for y in range(0, h, step_size):
        for x in range(0, w, step_size):
            dx, dy = optical_flow[y, x]
            cv2.arrowedLine(flow_img, (x, y), (int(x + dx), int(y + dy)), (0, 255, 0), 1, cv2.LINE_AA, tipLength=0.8)
    return optical_flow, flow_img


func.__name__ = "Gunnar-Farneback"
