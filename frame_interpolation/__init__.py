from .bicubic import func as bicubic
from .lanczos import func as lanczos
from .mitchell_netravali import func as mitchell_netravali
from .spline import func as spline

__all__ = ["bicubic", "spline", "lanczos", "mitchell_netravali"]