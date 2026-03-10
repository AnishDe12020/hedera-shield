from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def test_required_submission_docs_exist() -> None:
    assert (ROOT / "docs" / "DEPLOY_PROOF.md").is_file()
    assert (ROOT / "docs" / "TESTNET_SETUP.md").is_file()
    assert (ROOT / "docs" / "TESTNET_EVIDENCE.md").is_file()
    assert (ROOT / "docs" / "DEMO_RECORDING_RUNBOOK.md").is_file()
    assert (ROOT / "docs" / "FINAL_SUBMISSION_CHECKLIST.md").is_file()


def test_testnet_setup_references_deploy_proof_checklist() -> None:
    content = (ROOT / "docs" / "TESTNET_SETUP.md").read_text(encoding="utf-8")
    assert "DEPLOY_PROOF.md" in content
    assert "TESTNET_EVIDENCE.md" in content


def test_submission_references_testnet_evidence() -> None:
    content = (ROOT / "SUBMISSION.md").read_text(encoding="utf-8")
    assert "TESTNET_EVIDENCE.md" in content


def test_submission_references_demo_and_checklist_docs() -> None:
    content = (ROOT / "SUBMISSION.md").read_text(encoding="utf-8")
    assert "DEMO_RECORDING_RUNBOOK.md" in content
    assert "FINAL_SUBMISSION_CHECKLIST.md" in content


def test_readme_references_demo_and_checklist_docs() -> None:
    content = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "DEMO_RECORDING_RUNBOOK.md" in content
    assert "FINAL_SUBMISSION_CHECKLIST.md" in content
