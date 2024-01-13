import numpy as np
from scipy.ndimage import convolve
import cv2


def func(prev_frame, next_frame, a=1, num_iterations=10, bx=5, by=5):
    prev_frame_grayscale = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
    next_frame_grayscale = cv2.cvtColor(next_frame, cv2.COLOR_BGR2GRAY)

    prev_frame_grayscale = cv2.GaussianBlur(prev_frame_grayscale, (bx, by), 0)
    next_frame_grayscale = cv2.GaussianBlur(next_frame_grayscale, (bx, by), 0)

    prev_frame_grayscale = prev_frame_grayscale.astype(np.float32) / 255.0
    next_frame_grayscale = next_frame_grayscale.astype(np.float32) / 255.0

    kernel_x = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]])
    kernel_y = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]])

    dx = convolve(prev_frame_grayscale, kernel_x) + convolve(next_frame_grayscale, kernel_x)
    dy = convolve(prev_frame_grayscale, kernel_y) + convolve(next_frame_grayscale, kernel_y)
    dt = next_frame_grayscale - prev_frame_grayscale

    sigma = 1.0
    x = np.arange(-1, 2, 1)
    y = np.arange(-1, 2, 1)
    xx, yy = np.meshgrid(x, y)
    kernel_vel = np.exp(-(xx ** 2 + yy ** 2) / (2 * sigma ** 2))
    kernel_vel /= np.sum(kernel_vel)

    u, v = np.zeros_like(prev_frame_grayscale), np.zeros_like(prev_frame_grayscale)

    for _ in range(num_iterations):
        u_avg_vel = convolve(u, kernel_vel)
        v_avg_vel = convolve(v, kernel_vel)

        spatiotemporal_gradient = dx * u_avg_vel + dy * v_avg_vel + dt
        vel_norm = a ** 2 + u_avg_vel ** 2 + v_avg_vel ** 2
        u = u_avg_vel - spatiotemporal_gradient / vel_norm
        v = v_avg_vel - spatiotemporal_gradient / vel_norm

        u = np.clip(u, -1, 1)
        v = np.clip(v, -1, 1)

    optical_flow = np.stack((u, v), axis=-1)

    flow_img = np.copy(next_frame)
    h, w = flow_img.shape[:2]
    step_size = 20
    for y in range(0, h, step_size):
        for x in range(0, w, step_size):
            dx, dy = optical_flow[y, x] * 7
            cv2.arrowedLine(flow_img, (x, y), (int(x + dx), int(y + dy)), (0, 255, 0), 1, cv2.LINE_AA, tipLength=0.8)

    return optical_flow, flow_img


func.__name__ = "Horn-Schunck"
