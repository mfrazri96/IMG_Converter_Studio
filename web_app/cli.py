import argparse
import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INSTALL_HELP = (
    "Missing local web runtime dependency: {dependency}\n"
    "Install dependencies from the project root with:\n"
    "  python -m pip install -r requirements.txt\n"
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Easy IMG Studio locally.")
    parser.add_argument("--host", default=os.environ.get("EASY_IMG_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("EASY_IMG_PORT", "8000")))
    parser.add_argument("--reload", action="store_true", help="Restart the server when source files change.")
    args = parser.parse_args()

    try:
        import uvicorn
    except ModuleNotFoundError as exc:
        missing = exc.name or "uvicorn"
        parser.exit(1, INSTALL_HELP.format(dependency=missing))

    os.chdir(PROJECT_ROOT)
    uvicorn.run("web_app.app.main:app", host=args.host, port=args.port, reload=args.reload)
