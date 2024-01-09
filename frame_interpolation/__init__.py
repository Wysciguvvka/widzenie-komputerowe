from .bicubic import func as bicubic
from .lanczos import func as lanczos
from .spline import func as spline
from .avg import func as average_frame
__all__ = ["bicubic", "spline", "lanczos", "average_frame"]
