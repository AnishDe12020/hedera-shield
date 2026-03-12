# HederaShield Submission Handoff Matrix

Matrix timestamp (UTC): `2026-03-12T10:50:00Z`

## Step Matrix

| Submission step | Owner | Required artifact | Success criterion | Fallback action |
| --- | --- | --- | --- | --- |
| Run quick validation (`./scripts/pre-submit-verify.py`) | Submit Owner | `dist/pre-submit-verify-latest.txt` | `VERIFY|summary|PASS` appears | Stop submit flow, repair missing/failed evidence, rerun validation |
| Run pre-submit guard (`./scripts/pre_submit_guard.sh`) | Submit Owner | `dist/pre-submit-verify-latest.txt`, `dist/submission-readiness-latest.txt` | `GUARD|PASS` appears | Stop submit flow, restore required files/artifacts, rerun guard |
| Run submit-now checks (`./scripts/print_submit_now.sh`) | Submit Owner | `docs/evidence/submit-now/HEDERA_PORTAL_SUBMISSION_PACKET.json` and listed packet paths | No `CHECK|FAIL`; all required paths print `CHECK|PASS` | Stop submit flow, regenerate/repair missing submit-now artifacts |
| Capture submit-time commit SHA (`git rev-parse HEAD`) | Submit Owner | Local git commit SHA | SHA copied exactly for portal `Commit SHA` field | Stop before submit click and recopy SHA from terminal |
| Open canonical packet content | Submit Owner | `docs/evidence/submit-now/HEDERA_PORTAL_SUBMISSION_PACKET.json` | Packet opens and all fields are readable | Use `HEDERA_PORTAL_SUBMISSION_PACKET.md` fallback and re-verify field parity |
| Paste portal fields from packet | Submit Owner | Packet `fields.*` values | No wording drift; values match packet exactly | Abort entry, clear edited field, repaste from packet source |
| Replace placeholders before submit | Submit Owner | Final public demo URL and deployed URL (or `N/A`) | No `TODO_ADD_DEMO_VIDEO_URL` or `TODO_ADD_FINAL_DEPLOYED_URL_OR_NA` remains | Stop submit click until placeholders are replaced |
| Verify portal SHA equals local SHA | Submit Owner | Portal `Commit SHA` + local `git rev-parse HEAD` output | Exact SHA match confirmed | Stop submit click, correct portal SHA, re-verify |
| Click submit once | Submit Owner | Fully reviewed portal form | Single intentional submit click, no uncertain fields | Do not click; return to validation if uncertainty exists |
| Capture confirmation evidence immediately | Operator | Confirmation screenshot + UTC timestamp | Screenshot and UTC timestamp both recorded | Capture immediately; if missed, document gap and re-capture any available portal confirmation |
| Record submitted SHA + timestamp in handoff docs | Operator | Submitted SHA, UTC timestamp, evidence references | SHA/timestamp logged and linked for signoff | Block signoff until SHA/timestamp entries are completed |

## Cross-Linked Controls

- [SUBMISSION_CONFIDENCE_SUMMARY.md](SUBMISSION_CONFIDENCE_SUMMARY.md)
- [SUBMIT_OWNER_QUICK_CARD.md](SUBMIT_OWNER_QUICK_CARD.md)
- [OPERATOR_SIGNOFF_BRIEF.md](OPERATOR_SIGNOFF_BRIEF.md)
- [READY_TO_SUBMIT_STATUS.md](READY_TO_SUBMIT_STATUS.md)
- [SUBMISSION_GATE_REPORT.md](SUBMISSION_GATE_REPORT.md)
- [PORTAL_DRY_RUN_TRANSCRIPT.md](PORTAL_DRY_RUN_TRANSCRIPT.md)
