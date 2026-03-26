"""
Push local .env values to Railway variables.

Prerequisites:
- railway CLI installed and authenticated (`railway login`)
- Run from repo root where .env is located.

Usage examples:
    python scripts/push_env_to_railway.py --service backend
    python scripts/push_env_to_railway.py --service bot
    python scripts/push_env_to_railway.py --service backend --service bot

Notes:
- Secrets are read from your local .env and sent to Railway; .env must NOT be committed.
- We keep simple key filtering so TG_TOKEN уходит только в bot, остальные — в оба.
"""

import argparse
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / ".env"

BOT_ONLY = {"TG_TOKEN"}
BACKEND_ONLY = set()


def parse_env(path: Path) -> dict[str, str]:
    data = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        data[key.strip()] = val.strip()
    return data


def send_to_service(service: str, kv: dict[str, str]):
    if not kv:
        return
    args = ["railway", "variables", "set"]
    for k, v in kv.items():
        args.append(f"{k}={v}")
    subprocess.check_call(args + ["--service", service])


def main():
    parser = argparse.ArgumentParser(description="Push .env vars to Railway service")
    parser.add_argument(
        "--service",
        action="append",
        choices=["backend", "bot"],
        required=True,
        help="Target Railway service name",
    )
    args = parser.parse_args()

    if not ENV_PATH.exists():
        raise SystemExit(".env not found in repo root")

    env = parse_env(ENV_PATH)

    for service in args.service:
        kv = {}
        for k, v in env.items():
            if service == "bot" and (k in BOT_ONLY or k not in BACKEND_ONLY):
                kv[k] = v
            elif service == "backend" and (k in BACKEND_ONLY or k not in BOT_ONLY):
                kv[k] = v
        send_to_service(service, kv)
        print(f"Pushed {len(kv)} variables to service '{service}'")


if __name__ == "__main__":
    main()
