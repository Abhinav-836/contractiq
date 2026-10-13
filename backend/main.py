# main.py — root entry point for uvicorn
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from apps.api.main import app  # noqa: E402

__all__ = ["app"]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)