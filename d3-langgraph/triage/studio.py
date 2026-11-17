import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))  # lets "from graph import ..." work when loaded by path

from graph import build

graph = build().compile()   # no checkpointer: the dev server provides its own
