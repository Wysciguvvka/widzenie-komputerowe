import numpy as np
import cv2
from typing import Callable, Optional, Union, List, Dict


def pyramid_structure(optical_flow_func: Callable,
                      input_data: Union[str, List[np.ndarray]],
                      params: Optional[Dict[str, float]] = None,
                      debug: bool = False) -> Union[np.ndarray, List[np.ndarray]]:
    """
    Funkcja wykonuje piramidowy przepływ optyczny na podstawie podanej funkcji przepływu optycznego.

    Parametry:
        · optical_flow_func: Callable
            - Funkcja przepływu optycznego, która przyjmuje input_data, params i debug.
        · input_data: Union[str, List[np.ndarray]]
            - Jeśli jest to ścieżka do filmu, funkcja wczytuje klatki z filmu.
            - Jeśli jest to lista klatek (obiektów numpy.ndarray), funkcja używa tych klatek.
        · params: Optional[Dict[str, float]] = None
            - Parametry przekazywane do funkcji przepływu optycznego.
        · debug: bool = False
            - Określa, czy włączyć tryb debugowania.

    Zwraca:
        · Union[np.ndarray, List[np.ndarray]]
            - Wynik piramidowego przepływu optycznego.
    """
    try:
        if not callable(optical_flow_func):
            raise ValueError("Podana funkcja nie jest wywoływalna.")

        if isinstance(input_data, str):
            cap = cv2.VideoCapture(input_data)
            frames = []
            ret, frame = cap.read()
            while ret:
                frames.append(frame)
                ret, frame = cap.read()
            cap.release()

        elif isinstance(input_data, list) and all(isinstance(frame, np.ndarray) for frame in input_data):
            frames = input_data

        else:
            raise ValueError("Nieprawidłowe dane wejściowe. Oczekiwano ścieżki do filmu lub listy klatek.")

        pyramid = create_pyramid(frames)

        flow_pyramid = []
        for level in pyramid:
            flow = optical_flow_func(level, params, debug)
            flow_pyramid.append(flow)

        return flow_pyramid

    except ValueError as e:
        raise ValueError(f"Błąd podczas obliczeń piramidowego przepływu optycznego: {str(e)}")
    except Exception as e:
        raise ValueError(f"Niespodziewany błąd: {e}")


def create_pyramid(frames: List[np.ndarray], levels: int = 3) -> List[List[np.ndarray]]:
    """
    Funkcja tworzy piramidę klatek optycznych.

    Parametry:
        · frames: List[np.ndarray]
            - Lista klatek do utworzenia piramidy.
        · levels: int
            - Liczba poziomów piramidy.

    Zwraca:
        · List[List[np.ndarray]]
            - Piramida klatek optycznych.
    """
    pyramid = [frames]
    for _ in range(levels - 1):
        reduced_frames = [cv2.pyrDown(frame) for frame in pyramid[-1]]
        pyramid.append(reduced_frames)
    return pyramid
