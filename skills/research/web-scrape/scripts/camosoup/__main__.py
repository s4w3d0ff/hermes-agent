"""Allow running as python -m camosoup."""

import sys

from .cli import main

sys.exit(main())
