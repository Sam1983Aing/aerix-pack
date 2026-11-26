"""V02 export verification entry point."""
from pathlib import Path
import runpy
runpy.run_path(str(Path(__file__).with_name("verify_revision_export.py")))
