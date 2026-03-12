# HederaShield Freeze Checksum Ledger

Ledger timestamp (UTC): `2026-03-12T09:06:08Z`  
Audit branch: `master`  
Audit HEAD at capture: `4d2ac240149114bcf2d66fb5b5f4b34d4a4e3d00`

Purpose: docs-only freeze ledger for manual audit of key final artifacts using git-tracked references.

Reference format:
- `git_blob_sha1`: tracked blob hash (`git ls-files -s <path>`)
- `last_touch_commit`: latest commit touching path (`git log -1 --format=%H -- <path>`)

## Key Final Artifact References

| Path | git_blob_sha1 | last_touch_commit |
| --- | --- | --- |
| `docs/evidence/submission-freeze/validation-snapshot-latest.md` | `7ab9efb5fc9eaacc0c77764a83de5bd9425db163` | `753dad3a7dc0b19eb6e34e35b9ebf798694bc9a0` |
| `docs/evidence/submission-freeze/readiness-snapshot-latest.md` | `86eae3b408f6ae55b9a563f09898c337701f9a89` | `753dad3a7dc0b19eb6e34e35b9ebf798694bc9a0` |
| `docs/evidence/submission-freeze/portal-packet-snapshot-latest.md` | `caf342f3009a003adfdb61bc8c4b17f0f518657d` | `753dad3a7dc0b19eb6e34e35b9ebf798694bc9a0` |
| `docs/evidence/submission-freeze/submission-freeze-latest.md` | `ca0880ed2ece59e35fb5868d62f481ec7ceaa28e` | `753dad3a7dc0b19eb6e34e35b9ebf798694bc9a0` |
| `docs/evidence/submission-freeze/submission-freeze-latest.json` | `12793d8ab0f50f81f12b22d72cbf45278a05618c` | `753dad3a7dc0b19eb6e34e35b9ebf798694bc9a0` |
| `docs/evidence/submission-freeze/drift-verify-latest.md` | `4c0866223930d9d270dee17fdd554c235d346ed1` | `753dad3a7dc0b19eb6e34e35b9ebf798694bc9a0` |
| `docs/evidence/submission-freeze/drift-verify-latest.json` | `afc22bf3a4e613956b1b43d3e184a105e22aa997` | `753dad3a7dc0b19eb6e34e35b9ebf798694bc9a0` |
| `docs/evidence/submit-now/HEDERA_PORTAL_SUBMISSION_PACKET.json` | `015185a2034d0452ff5a845dc0eed5e0ffb90be5` | `b836843dda7b5adde2351122e06c4987f9642c12` |
| `docs/evidence/submit-now/SUBMIT_NOW_INDEX.md` | `1a28617b4d5cd3f698a0ce8026cc83743de54334` | `b836843dda7b5adde2351122e06c4987f9642c12` |
| `docs/evidence/submit-now/SUBMISSION_COMMANDS.md` | `47576bf845271b08f39f89b5f1d2511b4f1e85d6` | `446c1c6f083193bc93460220d14726c91a4839f7` |
| `dist/portal-submission/portal-submission-packet-latest.md` | `bd21c108b64bae2affbbc3fd15df522ac048bfe3` | `69166f00796ea8945a2e6eeb2d2a9d1bda0e3ac5` |
| `dist/portal-submission/portal-submission-verify-latest.txt` | `814cd7fb04766eee36c133e154b07c036be52b19` | `1f9d13f5f92b6f0cc9f426b37b4cedcfe945e740` |

## Check Snapshot (This Pass)

- `./scripts/submission-readiness.sh` -> `READINESS|summary|PASS`
- `./scripts/pre_submit_guard.sh` -> `GUARD|PASS|pre-submit guard complete (demo-id=3min-offline)`
- `./scripts/verify-portal-submission-packet.py` -> `PORTAL_VERIFY|summary|PASS|portal submission packet is ready`

## Control Links

- [RELEASE_FREEZE_NOTE.md](RELEASE_FREEZE_NOTE.md)
- [READY_TO_SUBMIT_STATUS.md](READY_TO_SUBMIT_STATUS.md)
- [EXEC_HANDOFF_DIGEST.md](EXEC_HANDOFF_DIGEST.md)
