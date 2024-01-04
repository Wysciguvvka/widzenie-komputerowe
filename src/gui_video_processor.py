from typing import List, Callable, Dict, Tuple

import numpy as np


def process_video(frames: List, optical_flow: Callable, optical_flows_args: Dict, interpolation: Callable,
                  interpolation_args: Dict) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """

    :param frames: list of frames
    :param optical_flow: optical flow function
    :param optical_flows_args: kwargs for optical flow function
    :param interpolation: interpolation function
    :param interpolation_args: kwargs for interpolation function
    :return: visualization of flow, interpolated frames, video with generated frames
    """
    interpolated_frames = []
    flow_video = []
    new_video = [frames[0]]
    for i in range(1, len(frames)):
        prev_frame = frames[i - 1]
        next_frame = frames[i]

        fw_flow, fw_of_img = optical_flow(prev_frame, next_frame, **optical_flows_args)
        flow_video.append(fw_of_img)
        ip_frame = interpolation(prev_frame, next_frame, fw_flow, **interpolation_args)
        interpolated_frames.append(ip_frame)
        new_video.append(ip_frame)
        new_video.append(next_frame)

    return np.array(flow_video), np.array(interpolated_frames), np.array(new_video)


if __name__ == '__main__':
    import cv2
    from optical_flow import gunnar_farneback
    from frame_interpolation import bicubic

    video_path = '../video/slow_traffic_small.mp4'
    cap: cv2.VideoCapture = cv2.VideoCapture(video_path)
    _frames: List[np.ndarray] = []
    ret: bool
    frame: np.ndarray
    ret, frame = cap.read()
    fps = cap.get(cv2.CAP_PROP_FPS)
    print(fps)
    while ret:
        _frames.append(frame)
        ret, frame = cap.read()
    cap.release()
    _frames = _frames[:290]
    _, __, new_vid = process_video(_frames, gunnar_farneback, {}, bicubic, {})
    fourcc = cv2.VideoWriter.fourcc(*"mp4v")
    height, width, _ = new_vid[0].shape
    out = cv2.VideoWriter(f"../results/test.mp4", fourcc, 2 * fps, (width, height))

    for frame in new_vid:
        out.write(frame)
    out.release()
    print('---')
    print(len(_frames))
    print(len(new_vid))
    height, width, _ = _frames[0].shape
    out = cv2.VideoWriter(f"../results/original.mp4", fourcc, fps, (width, height))

    for frame in _frames:
        out.write(frame)
    out.release()
