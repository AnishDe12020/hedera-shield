#!/usr/bin/env python3
"""Validate HederaShield testnet env files without network calls."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Iterable

REQUIRED_VARS: tuple[str, ...] = (
    "HEDERA_SHIELD_HEDERA_NETWORK",
    "HEDERA_SHIELD_HEDERA_OPERATOR_ID",
    "HEDERA_SHIELD_HEDERA_OPERATOR_KEY",
    "HEDERA_SHIELD_MIRROR_NODE_URL",
    "HEDERA_SHIELD_MIRROR_NODE_POLL_INTERVAL",
    "HEDERA_SHIELD_ANTHROPIC_API_KEY",
    "HEDERA_SHIELD_AI_MODEL",
    "HEDERA_SHIELD_LARGE_TRANSFER_THRESHOLD",
    "HEDERA_SHIELD_VELOCITY_WINDOW_SECONDS",
    "HEDERA_SHIELD_VELOCITY_MAX_TRANSFERS",
    "HEDERA_SHIELD_API_HOST",
    "HEDERA_SHIELD_API_PORT",
    "HEDERA_SHIELD_MONITORED_TOKEN_IDS",
    "HEDERA_SHIELD_SANCTIONED_ADDRESSES",
)

ACCOUNT_ID_RE = re.compile(r"^\d+\.\d+\.\d+$")
ACCOUNT_ID_PLACEHOLDER_RE = re.compile(r"^0\.0\.(YOUR_[A-Z0-9_]+|PLACEHOLDER|EXAMPLE)$")
KEY_PLACEHOLDER_RE = re.compile(r"^(YOUR_[A-Z0-9_]+|your_[a-z0-9_]+|<[^>]+>)$")
HEX_KEY_RE = re.compile(r"^(0x)?[0-9a-fA-F]{64,128}$")


def _strip_inline_comment(value: str) -> str:
    if " #" in value:
        return value.split(" #", 1)[0].strip()
    return value.strip()


def load_env(path: Path) -> dict[str, str]:
    env: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue

        key, value = line.split("=", 1)
        env[key.strip()] = _strip_inline_comment(value)
    return env


def is_valid_account_id_or_placeholder(value: str) -> bool:
    return bool(ACCOUNT_ID_RE.fullmatch(value) or ACCOUNT_ID_PLACEHOLDER_RE.fullmatch(value))


def is_valid_key_or_placeholder(value: str) -> bool:
    if KEY_PLACEHOLDER_RE.fullmatch(value):
        return True
    if HEX_KEY_RE.fullmatch(value):
        return True

    # Base64-like allowance for SDK-exported key strings.
    if len(value) >= 40 and re.fullmatch(r"[A-Za-z0-9+/=]+", value):
        return True

    return False


def _validate_json_account_id_list(raw: str, var_name: str, errors: list[str]) -> None:
    try:
        items = json.loads(raw)
    except json.JSONDecodeError as exc:
        errors.append(f"{var_name} must be valid JSON: {exc.msg}")
        return

    if not isinstance(items, list):
        errors.append(f"{var_name} must be a JSON array")
        return

    for idx, item in enumerate(items):
        if not isinstance(item, str) or not is_valid_account_id_or_placeholder(item):
            errors.append(
                f"{var_name}[{idx}] must be Hedera account ID (0.0.x) or placeholder; got: {item!r}"
            )


def validate_env_map(env: dict[str, str]) -> list[str]:
    errors: list[str] = []

    missing = [name for name in REQUIRED_VARS if name not in env]
    for name in missing:
        errors.append(f"Missing required variable: {name}")

    if errors:
        return errors

    if env["HEDERA_SHIELD_HEDERA_NETWORK"] not in {"testnet", "mainnet", "previewnet"}:
        errors.append("HEDERA_SHIELD_HEDERA_NETWORK must be one of: testnet, mainnet, previewnet")

    operator_id = env["HEDERA_SHIELD_HEDERA_OPERATOR_ID"]
    if not is_valid_account_id_or_placeholder(operator_id):
        errors.append(
            "HEDERA_SHIELD_HEDERA_OPERATOR_ID must be Hedera account ID (0.0.x) or placeholder like 0.0.YOUR_OPERATOR_ACCOUNT_ID"
        )

    operator_key = env["HEDERA_SHIELD_HEDERA_OPERATOR_KEY"]
    if not is_valid_key_or_placeholder(operator_key):
        errors.append(
            "HEDERA_SHIELD_HEDERA_OPERATOR_KEY must be plausible key material or placeholder like YOUR_ED25519_PRIVATE_KEY"
        )

    for int_var in (
        "HEDERA_SHIELD_MIRROR_NODE_POLL_INTERVAL",
        "HEDERA_SHIELD_VELOCITY_WINDOW_SECONDS",
        "HEDERA_SHIELD_VELOCITY_MAX_TRANSFERS",
        "HEDERA_SHIELD_API_PORT",
    ):
        try:
            int(env[int_var])
        except ValueError:
            errors.append(f"{int_var} must be an integer")

    try:
        float(env["HEDERA_SHIELD_LARGE_TRANSFER_THRESHOLD"])
    except ValueError:
        errors.append("HEDERA_SHIELD_LARGE_TRANSFER_THRESHOLD must be a number")

    _validate_json_account_id_list(env["HEDERA_SHIELD_SANCTIONED_ADDRESSES"], "HEDERA_SHIELD_SANCTIONED_ADDRESSES", errors)

    try:
        token_ids = json.loads(env["HEDERA_SHIELD_MONITORED_TOKEN_IDS"])
        if not isinstance(token_ids, list):
            errors.append("HEDERA_SHIELD_MONITORED_TOKEN_IDS must be a JSON array")
        else:
            for idx, value in enumerate(token_ids):
                if not isinstance(value, str) or not is_valid_account_id_or_placeholder(value):
                    errors.append(
                        f"HEDERA_SHIELD_MONITORED_TOKEN_IDS[{idx}] must be token ID/account-style string (0.0.x or placeholder); got: {value!r}"
                    )
    except json.JSONDecodeError as exc:
        errors.append(f"HEDERA_SHIELD_MONITORED_TOKEN_IDS must be valid JSON: {exc.msg}")

    return errors


def validate_env_file(path: Path) -> list[str]:
    if not path.exists():
        return [f"Env file not found: {path}"]
    env = load_env(path)
    return validate_env_map(env)


def _format_errors(errors: Iterable[str]) -> str:
    return "\n".join(f"- {error}" for error in errors)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate HederaShield testnet env format (offline)")
    parser.add_argument(
        "env_file",
        nargs="?",
        default=".env.testnet",
        help="Path to env file to validate (default: .env.testnet)",
    )
    args = parser.parse_args()

    errors = validate_env_file(Path(args.env_file))
    if errors:
        print("Validation failed:")
        print(_format_errors(errors))
        return 1

    print("Validation passed: env format is compatible with offline testnet setup.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
