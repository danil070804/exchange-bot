import os
import signal
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "apps" / "backend"


def _terminate(process: subprocess.Popen | None) -> None:
    if process is None or process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()


def main() -> int:
    port = os.getenv("PORT", "8000")
    current_backend_url = os.getenv("BACKEND_API_URL", "").strip()
    if not current_backend_url or "127.0.0.1" in current_backend_url or "localhost" in current_backend_url:
        os.environ["BACKEND_API_URL"] = f"http://127.0.0.1:{port}"

    migrate = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=BACKEND_DIR,
        check=False,
    )
    if migrate.returncode != 0:
        return migrate.returncode

    backend = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", port],
        cwd=BACKEND_DIR,
        env=os.environ.copy(),
    )

    time.sleep(3)

    bot = subprocess.Popen(
        [sys.executable, "-m", "bot.main"],
        cwd=ROOT,
        env=os.environ.copy(),
    )

    def handle_signal(signum, frame):
        _terminate(bot)
        _terminate(backend)
        raise SystemExit(0)

    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)

    try:
        while True:
            backend_code = backend.poll()
            bot_code = bot.poll()

            if backend_code is not None:
                _terminate(bot)
                return backend_code
            if bot_code is not None:
                _terminate(backend)
                return bot_code

            time.sleep(1)
    finally:
        _terminate(bot)
        _terminate(backend)


if __name__ == "__main__":
    raise SystemExit(main())