import numpy as np
from typing import Callable, Optional, Union, List, Dict


def func(optical_flow_func: Callable,
         input_data: Union[str, List[np.ndarray]],
         params: Optional[Dict[str, float]] = None,
         debug: bool = False) -> Union[np.ndarray, List[np.ndarray]]:
    """
    Funkcja wykonuje przepływ optyczny na podstawie podanej funkcji.

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
            - Wynik funkcji przepływu optycznego.
    """
    try:
        if not callable(optical_flow_func):
            raise ValueError("Podana funkcja nie jest wywoływalna.")

        if not isinstance(input_data, (str, list)) or \
                (isinstance(input_data, list) and not all(isinstance(frame, np.ndarray) for frame in input_data)):
            raise ValueError("Nieprawidłowe dane wejściowe. Oczekiwano ścieżki do filmu lub listy zdjęć.")

        return optical_flow_func(input_data, params, debug)

    except ValueError as e:
        raise ValueError(f"Błąd podczas obliczeń przepływu optycznego: {str(e)}")
    except Exception as e:
        raise ValueError(f"Niespodziewany błąd: {e}")
