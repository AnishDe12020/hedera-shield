"""Loads compliance rules from YAML/JSON configuration files."""

import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Default config location relative to project root
_DEFAULT_RULES_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "config",
    "rules.yaml",
)

# Inline defaults used when no YAML file is found
_FALLBACK_CONFIG: dict[str, Any] = {
    "large_transfer": {
        "enabled": True,
        "severity": "high",
        "default_threshold": 10000.0,
        "token_thresholds": {},
        "recommended_action": "freeze",
    },
    "velocity": {
        "enabled": True,
        "severity": "medium",
        "window_seconds": 3600,
        "max_transfers": 50,
        "token_overrides": {},
        "recommended_action": "freeze",
    },
    "sanctions": {
        "enabled": True,
        "severity": "critical",
        "file": "",
        "inline_addresses": [],
        "recommended_action": "freeze",
    },
    "round_number": {
        "enabled": True,
        "severity": "medium",
        "minimum_amount": 1000.0,
        "divisors": [50000.0, 10000.0, 5000.0, 1000.0],
        "recommended_action": "none",
    },
    "rapid_succession": {
        "enabled": True,
        "severity": "high",
        "window_seconds": 10,
        "min_transfers": 3,
        "recommended_action": "freeze",
    },
    "structuring": {
        "enabled": True,
        "severity": "high",
        "window_seconds": 7200,
        "min_count": 3,
        "threshold_pct": 0.9,
        "recommended_action": "freeze",
    },
    "dormant_account": {
        "enabled": True,
        "severity": "medium",
        "dormancy_seconds": 2592000,  # 30 days
        "min_amount": 1000.0,
        "recommended_action": "kyc_revoke",
    },
    "cross_token_wash": {
        "enabled": True,
        "severity": "high",
        "window_seconds": 3600,
        "min_tokens": 3,
        "recommended_action": "freeze",
    },
    "risk_score_calibration": {
        "default": {
            "multiplier": 1.0,
            "offset": 0.0,
            "min": 0.0,
            "max": 1.0,
        },
        "by_alert_type": {},
    },
}


def _deep_merge(base: dict, override: dict) -> dict:
    """Recursively merge *override* into a copy of *base*."""
    merged = dict(base)
    for key, value in override.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_rules_config(path: str | None = None) -> dict[str, Any]:
    """Load and return the rules configuration dictionary.

    Parameters
    ----------
    path : str | None
        Path to a YAML or JSON rules file.  When *None* the loader
        looks for ``config/rules.yaml`` relative to the project root.
        If no file is found the built-in fallback defaults are used.

    Returns
    -------
    dict[str, Any]
        Merged configuration (fallback defaults + file overrides).
    """
    config_path = path or _DEFAULT_RULES_PATH

    file_config: dict[str, Any] = {}
    if os.path.isfile(config_path):
        _, ext = os.path.splitext(config_path.lower())
        if ext == ".json":
            import json

            try:
                with open(config_path, "r") as fh:
                    file_config = json.load(fh) or {}
                logger.info("Loaded rules config from %s", config_path)
            except Exception as exc:
                logger.error("Failed to load rules config from %s: %s", config_path, exc)
        else:
            try:
                import yaml  # type: ignore[import-untyped]

                with open(config_path, "r") as fh:
                    file_config = yaml.safe_load(fh) or {}
                logger.info("Loaded rules config from %s", config_path)
            except ImportError:
                logger.warning(
                    "pyyaml is not installed; falling back to built-in defaults. "
                    "Install with: pip install pyyaml"
                )
            except Exception as exc:
                logger.error("Failed to load rules config from %s: %s", config_path, exc)
    else:
        # Try JSON as a fallback
        json_path = config_path.rsplit(".", 1)[0] + ".json" if "." in config_path else config_path + ".json"
        if os.path.isfile(json_path):
            import json

            try:
                with open(json_path, "r") as fh:
                    file_config = json.load(fh)
                logger.info("Loaded rules config from %s", json_path)
            except Exception as exc:
                logger.error("Failed to load rules config from %s: %s", json_path, exc)
        else:
            logger.info(
                "No rules config file found at %s; using built-in defaults",
                config_path,
            )

    return _deep_merge(_FALLBACK_CONFIG, file_config)


def load_sanctions_list(config: dict[str, Any]) -> set[str]:
    """Load sanctioned addresses from the sanctions config section.

    Merges addresses from the external file (if specified) and inline list.

    Parameters
    ----------
    config : dict
        The ``sanctions`` section of the rules config.

    Returns
    -------
    set[str]
        Unique sanctioned account IDs.
    """
    addresses: set[str] = set()

    # Load from file
    sanctions_file = config.get("file", "")
    if sanctions_file:
        # Resolve relative paths from the project root
        if not os.path.isabs(sanctions_file):
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            sanctions_file = os.path.join(project_root, sanctions_file)

        if os.path.isfile(sanctions_file):
            try:
                with open(sanctions_file, "r") as fh:
                    for line in fh:
                        stripped = line.strip()
                        if stripped and not stripped.startswith("#"):
                            addresses.add(stripped)
                logger.info(
                    "Loaded %d sanctioned addresses from %s",
                    len(addresses),
                    sanctions_file,
                )
            except Exception as exc:
                logger.error("Failed to read sanctions file %s: %s", sanctions_file, exc)
        else:
            logger.warning("Sanctions file not found: %s", sanctions_file)

    # Merge inline addresses
    inline = config.get("inline_addresses", [])
    if inline:
        addresses.update(inline)

    return addresses
