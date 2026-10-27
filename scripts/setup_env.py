"""Create .env from .env.example and fill in generated secrets (used by `make setup`).

make.ps1 does the same natively in PowerShell, so Windows needs no Python on the host.
Existing values in .env are kept; only empty secrets are generated.
"""

from __future__ import annotations

import re
import secrets
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SECRETS = ("POSTGRES_PASSWORD", "APP_DB_PASSWORD", "POWERBI_DB_PASSWORD", "JWT_SECRET")


def main() -> int:
    env = ROOT / ".env"
    if not env.exists():
        env.write_text((ROOT / ".env.example").read_text(encoding="utf-8"), encoding="utf-8")
        print("Created .env from .env.example")
    text = env.read_text(encoding="utf-8")
    for key in SECRETS:
        pattern = re.compile(rf"^{key}=\s*(#.*)?$", re.MULTILINE)
        if pattern.search(text):
            text = pattern.sub(f"{key}={secrets.token_urlsafe(24)}", text)
            print(f"Generated {key}")
    if re.search(r"^DEMO_PASSWORDS=\s*(#.*)?$", text, re.MULTILINE):
        users = re.findall(r"user_id:\s*([\w.]+)", (ROOT / "config" / "demo.yaml").read_text(encoding="utf-8")) + ["pipeline"]
        alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789"
        pairs = ",".join(f"{u}={'-'.join(''.join(secrets.choice(alphabet) for _ in range(5)) for _ in range(4))}" for u in users)
        text = re.sub(r"^DEMO_PASSWORDS=.*$", lambda _: f"DEMO_PASSWORDS={pairs}", text, flags=re.MULTILINE)
        print(f"Generated passwords for {len(users)} test accounts (DEMO_PASSWORDS)")
    if len(sys.argv) > 1 and sys.argv[1] == "--local":
        # Running without Docker: keep data inside the repository and use mock models.
        text = re.sub(r"^DATA_ROOT=.*$", "DATA_ROOT=./.data", text, flags=re.MULTILINE)
        text = re.sub(r"^LLM_MODE=.*$", "LLM_MODE=mock", text, flags=re.MULTILINE)
    env.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
