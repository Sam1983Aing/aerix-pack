"""V02 comparison and teaching archive entry point."""
from pathlib import Path
import runpy
runpy.run_path(str(Path(__file__).with_name("compare_revision.py")))
