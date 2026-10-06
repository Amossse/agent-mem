"""Package entry point for the self-contained skill script."""

import runpy
from pathlib import Path


def main(argv=None):
    script = Path(__file__).parent / "skills/agent-mem/scripts/mem.py"
    return runpy.run_path(str(script))["main"](argv)


if __name__ == "__main__":
    raise SystemExit(main())
