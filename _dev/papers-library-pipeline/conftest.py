import sys
from pathlib import Path

# repo/_dev/papers-library-pipeline/conftest.py → repo/skills/papers-library-pipeline/scripts
_SCRIPTS = (
    Path(__file__).resolve().parents[2]
    / "skills"
    / "papers-library-pipeline"
    / "scripts"
)
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
