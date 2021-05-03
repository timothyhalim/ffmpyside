import os
try:
    FILEDIR = os.path.dirname(__file__)
except:
    import inspect
    FILEDIR = os.path.dirname(inspect.getframeinfo(inspect.currentframe()).filename)

os.environ['FFMPEG'] = os.path.normpath(os.path.join(FILEDIR, "bin","ffmpeg.exe")).replace("\\", "/")
os.environ['FFPROBE'] = os.path.normpath(os.path.join(FILEDIR, "bin","ffprobe.exe")).replace("\\", "/")

from . import nodes
from . import _ffmpeg
from . import _filters
from . import _probe
from . import _run
from . import _view
from .nodes import *
from ._ffmpeg import *
from ._filters import *
from ._probe import *
from ._run import *
from ._view import *

__all__ = (
    nodes.__all__
    + _ffmpeg.__all__
    + _probe.__all__
    + _run.__all__
    + _view.__all__
    + _filters.__all__
)