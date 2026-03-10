# Human Handoff Playbook Generator

Generates an execution-ready manual handoff plan for the remaining hackathon submission steps (record demo, fill portal form, final submit).

## Command

```bash
./scripts/generate-human-handoff-playbook.sh
```

Optional flags:

```bash
./scripts/generate-human-handoff-playbook.sh \
  --timestamp "$(date -u +%Y%m%dT%H%M%SZ)" \
  --demo-video-url "https://youtu.be/<video-id>" \
  --portal-submission-url "https://<hackathon-portal>/submission/<id>"
```

## Outputs

- `dist/handoff-playbook/<timestamp>/human-handoff-playbook.md`
- `dist/handoff-playbook/<timestamp>/human-handoff-playbook.json`
- `dist/handoff-playbook/human-handoff-playbook-latest.md`
- `dist/handoff-playbook/human-handoff-playbook-latest.json`

## Readiness Gate

The generator marks blockers when required artifacts are missing or critical manual fields are still placeholders (for example demo video URL).

If blockers are open, follow the checkboxes/commands in the generated markdown and regenerate until readiness is `READY`.
