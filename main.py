from typing import Union, List, Dict, Callable, Optional
import cv2
import inspect
import numpy as np
import datetime
import os
import optical_flow.algorithms.sparse as sparse
import optical_flow.algorithms.dense as dense
import optical_flow.structure as structure
import optical_flow.models as models
import frame_interpolation as interpolation


def process_video(input_data: Union[str, List[np.ndarray]],
                  optical_flow_func: Callable,
                  structure_func: Callable,
                  interpolation_func: Callable,
                  flow_params: Optional[Dict[str, float]] = None,
                  interpolation_params: Optional[Dict[str, float]] = None,
                  pyramid_levels: Optional[int] = None) -> None:
    """
    Funkcja przetwarza wideo, zapisując zinterpolowany film do folderu.

    Parametry:
        · input_data: Union[str, List[np.ndarray]]
            - Jeśli jest to ścieżka do filmu, funkcja wczytuje klatki z filmu.
            - Jeśli jest to lista klatek (obiektów numpy.ndarray), funkcja używa tych klatek.
        · optical_flow_func: Callable
            - Funkcja przepływu optycznego, która przyjmuje input_data, params i debug.
        · structure_func: Callable
            - Funkcja struktury do przepływu optycznego.
        · interpolation_func: Callable
            - Funkcja interpolacji klatek.
        · flow_params: Optional[Dict[str, float]] = None
            - Parametry przekazywane do funkcji przepływu optycznego.
        · interpolation_params: Optional[Dict[str, float]] = None
            - Parametry przekazywane do funkcji interpolacji.
        · pyramid_levels: Optional[int] = None
            - Ilość poziomów piramidy (używane tylko gdy struktura jest piramidowa).

    Zwraca:
        · None, film jest zapisywany do folderu
    """
    try:
        if isinstance(input_data, str):
            cap: cv2.VideoCapture = cv2.VideoCapture(input_data)
            frames: List[np.ndarray] = []
            ret: bool
            frame: np.ndarray
            ret, frame = cap.read()
            while ret:
                frames.append(frame)
                ret, frame = cap.read()
            cap.release()
        elif isinstance(input_data, list) and all(isinstance(frame, np.ndarray) for frame in input_data):
            frames = input_data
        else:
            raise ValueError("Nieprawidłowe dane wejściowe. Oczekiwano ścieżki do filmu lub listy zdjęć")

        frames_copy = [frame.copy() for frame in frames]
        if is_parameter_present(structure_func, "levels"):
            optical_flow_frames: Union[np.ndarray, List[np.ndarray]] = structure_func(optical_flow_func, frames_copy,
                                                                                      flow_params,
                                                                                      levels=pyramid_levels)
        else:
            optical_flow_frames: Union[np.ndarray, List[np.ndarray]] = structure_func(optical_flow_func, frames_copy,
                                                                                      flow_params)

        interpolated_frames: List[np.ndarray] = interpolation_func(frames_copy, optical_flow_frames, 2)

        h, w, _ = frames[0].shape
        debug_video: np.ndarray = np.zeros((h, w * 2, 3), dtype=np.uint8)
        for i in range(len(frames)):
            debug_video[:, :w, :] = frames[i]
            debug_video[:, w:, :] = interpolated_frames[i]

            cv2.imshow('Debug Video', debug_video)
            if cv2.waitKey(30) & 0xFF == 27:  # ESC key to exit
                break

        current_time = datetime.datetime.now()
        time_str = current_time.strftime("%H_%M_%S_%d_%m")

        height, width, _ = interpolated_frames[0].shape
        fourcc = cv2.VideoWriter.fourcc(*"mp4v")
        out = cv2.VideoWriter(f"results/{time_str}.mp4", fourcc, 30.0, (width, height))

        for frame in interpolated_frames:
            out.write(frame)
        out.release()

    except cv2.error as e:
        raise ValueError(f"Błąd OpenCV: {e}")
    except Exception as e:
        raise ValueError(f"Niespodziewany błąd: {e}")


def is_parameter_present(function: Callable, parameter_name: str) -> bool:
    parameters = inspect.signature(function).parameters
    return parameter_name in parameters


if __name__ == "__main__":
    process_video("slow_traffic_small.mp4",
                  sparse.lucas_kanade,
                  structure.onewaystructure,
                  interpolation.bicubic)
