from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def test_required_submission_docs_exist() -> None:
    assert (ROOT / "docs" / "DEPLOY_PROOF.md").is_file()
    assert (ROOT / "docs" / "TESTNET_SETUP.md").is_file()


def test_testnet_setup_references_deploy_proof_checklist() -> None:
    content = (ROOT / "docs" / "TESTNET_SETUP.md").read_text(encoding="utf-8")
    assert "DEPLOY_PROOF.md" in content
