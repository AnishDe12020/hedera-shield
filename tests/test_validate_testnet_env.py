from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parent.parent / "scripts" / "validate-testnet-env.py"
_spec = importlib.util.spec_from_file_location("validate_testnet_env", SCRIPT_PATH)
if _spec is None or _spec.loader is None:
    raise RuntimeError(f"Unable to load validator script from {SCRIPT_PATH}")
validator = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(validator)


def _valid_env_map() -> dict[str, str]:
    return {
        "HEDERA_SHIELD_HEDERA_NETWORK": "testnet",
        "HEDERA_SHIELD_HEDERA_OPERATOR_ID": "0.0.YOUR_OPERATOR_ACCOUNT_ID",
        "HEDERA_SHIELD_HEDERA_OPERATOR_KEY": "YOUR_ED25519_PRIVATE_KEY",
        "HEDERA_SHIELD_MIRROR_NODE_URL": "https://testnet.mirrornode.hedera.com",
        "HEDERA_SHIELD_MIRROR_NODE_POLL_INTERVAL": "10",
        "HEDERA_SHIELD_ANTHROPIC_API_KEY": "YOUR_ANTHROPIC_API_KEY_OR_EMPTY",
        "HEDERA_SHIELD_AI_MODEL": "claude-sonnet-4-20250514",
        "HEDERA_SHIELD_LARGE_TRANSFER_THRESHOLD": "10000",
        "HEDERA_SHIELD_VELOCITY_WINDOW_SECONDS": "3600",
        "HEDERA_SHIELD_VELOCITY_MAX_TRANSFERS": "50",
        "HEDERA_SHIELD_API_HOST": "0.0.0.0",
        "HEDERA_SHIELD_API_PORT": "8000",
        "HEDERA_SHIELD_MONITORED_TOKEN_IDS": '["0.0.YOUR_TOKEN_ID"]',
        "HEDERA_SHIELD_SANCTIONED_ADDRESSES": '["0.0.YOUR_SANCTIONED_ACCOUNT_ID"]',
    }


def test_account_id_format_accepts_numeric_and_placeholder() -> None:
    assert validator.is_valid_account_id_or_placeholder("0.0.123456")
    assert validator.is_valid_account_id_or_placeholder("0.0.YOUR_OPERATOR_ACCOUNT_ID")


def test_account_id_format_rejects_invalid_values() -> None:
    assert not validator.is_valid_account_id_or_placeholder("0.0.-1")
    assert not validator.is_valid_account_id_or_placeholder("abc")


def test_key_format_accepts_placeholder_and_hex() -> None:
    assert validator.is_valid_key_or_placeholder("YOUR_ED25519_PRIVATE_KEY")
    assert validator.is_valid_key_or_placeholder("a" * 64)


def test_key_format_rejects_invalid_values() -> None:
    assert not validator.is_valid_key_or_placeholder("not-a-key")


def test_validate_env_map_passes_for_placeholder_testnet_values() -> None:
    errors = validator.validate_env_map(_valid_env_map())
    assert errors == []


def test_validate_env_map_fails_for_invalid_operator_id() -> None:
    env = _valid_env_map()
    env["HEDERA_SHIELD_HEDERA_OPERATOR_ID"] = "invalid-account"
    errors = validator.validate_env_map(env)
    assert any("HEDERA_SHIELD_HEDERA_OPERATOR_ID" in error for error in errors)


def test_validate_env_map_fails_for_invalid_key_placeholder() -> None:
    env = _valid_env_map()
    env["HEDERA_SHIELD_HEDERA_OPERATOR_KEY"] = "KEY_PLACEHOLDER"
    errors = validator.validate_env_map(env)
    assert any("HEDERA_SHIELD_HEDERA_OPERATOR_KEY" in error for error in errors)


def test_validate_env_map_fails_for_missing_required_variable() -> None:
    env = _valid_env_map()
    env.pop("HEDERA_SHIELD_API_PORT")
    errors = validator.validate_env_map(env)
    assert any("Missing required variable: HEDERA_SHIELD_API_PORT" == error for error in errors)


def test_validate_env_file_parses_inline_comments(tmp_path: Path) -> None:
    env_file = tmp_path / ".env.testnet"
    env_file.write_text(
        "\n".join(
            [
                "HEDERA_SHIELD_HEDERA_NETWORK=testnet  # required",
                "HEDERA_SHIELD_HEDERA_OPERATOR_ID=0.0.YOUR_OPERATOR_ACCOUNT_ID  # placeholder",
                "HEDERA_SHIELD_HEDERA_OPERATOR_KEY=YOUR_ED25519_PRIVATE_KEY  # placeholder",
                "HEDERA_SHIELD_MIRROR_NODE_URL=https://testnet.mirrornode.hedera.com",
                "HEDERA_SHIELD_MIRROR_NODE_POLL_INTERVAL=10",
                "HEDERA_SHIELD_ANTHROPIC_API_KEY=YOUR_ANTHROPIC_API_KEY_OR_EMPTY",
                "HEDERA_SHIELD_AI_MODEL=claude-sonnet-4-20250514",
                "HEDERA_SHIELD_LARGE_TRANSFER_THRESHOLD=10000",
                "HEDERA_SHIELD_VELOCITY_WINDOW_SECONDS=3600",
                "HEDERA_SHIELD_VELOCITY_MAX_TRANSFERS=50",
                "HEDERA_SHIELD_API_HOST=0.0.0.0",
                "HEDERA_SHIELD_API_PORT=8000",
                'HEDERA_SHIELD_MONITORED_TOKEN_IDS=["0.0.YOUR_TOKEN_ID"]',
                'HEDERA_SHIELD_SANCTIONED_ADDRESSES=["0.0.YOUR_SANCTIONED_ACCOUNT_ID"]',
            ]
        ),
        encoding="utf-8",
    )

    assert validator.validate_env_file(env_file) == []
