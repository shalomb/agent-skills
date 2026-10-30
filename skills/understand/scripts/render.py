#!/usr/bin/env python3
"""Run the renderer without installing it: python scripts/render.py BUNDLE OUT --source-root DIR."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from understand_render.cli import main  # noqa: E402

sys.exit(main())
