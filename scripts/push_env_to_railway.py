"""
Push local .env values to Railway variables.

Prerequisites:
- railway CLI installed and authenticated (`railway login`)
- Run from repo root where .env is located.

Usage examples:
    python scripts/push_env_to_railway.py --service backend
    python scripts/push_env_to_railway.py --service bot
    python scripts/push_env_to_railway.py --service backend --service bot
    python scripts/push_env_to_railway.py --service exchange-bot

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
MINIAPP_ONLY_PREFIXES = ("VITE_",)


def is_local_value(value: str) -> bool:
    v = value.lower()
    return "localhost" in v or "127.0.0.1" in v


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


def filter_local_infra_vars_for_railway(service: str, kv: dict[str, str]) -> tuple[dict[str, str], list[str]]:
    """Drop localhost DB/Redis values to avoid breaking Railway deployments."""
    if service not in {"backend", "exchange-bot"}:
        return kv, []

    dropped = []
    filtered = dict(kv)
    for key in ("DATABASE_URL", "REDIS_URL"):
        value = filtered.get(key)
        if value and is_local_value(value):
            dropped.append(key)
            filtered.pop(key, None)
    return filtered, dropped


def main():
    parser = argparse.ArgumentParser(description="Push .env vars to Railway service")
    parser.add_argument(
        "--service",
        action="append",
        choices=["backend", "bot", "exchange-bot", "miniapp"],
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
            if service == "exchange-bot":
                kv[k] = v
            elif service == "miniapp" and any(k.startswith(prefix) for prefix in MINIAPP_ONLY_PREFIXES):
                kv[k] = v
            elif service == "bot" and (k in BOT_ONLY or k not in BACKEND_ONLY):
                kv[k] = v
            elif service == "backend" and (k in BACKEND_ONLY or k not in BOT_ONLY):
                kv[k] = v
        kv, dropped = filter_local_infra_vars_for_railway(service, kv)
        send_to_service(service, kv)
        print(f"Pushed {len(kv)} variables to service '{service}'")
        if dropped:
            print(
                "Skipped local-only vars for Railway "
                f"service '{service}': {', '.join(dropped)}. "
                "Set them from linked Railway Postgres/Redis variables instead."
            )


if __name__ == "__main__":
    main()
