# Offline Restore and Apply

Package directory: artifacts/offline-handoff/20260310T160000Z

## Option 1: Restore using git bundle
1. Copy `offline.bundle` to target machine.
2. In target repo:

   ```bash
   git fetch /path/to/offline.bundle "master"
   git checkout -B "master" FETCH_HEAD
   ```

## Option 2: Apply patch series
1. Copy `patches/*.patch` to target machine.
2. In target repo on desired base branch:

   ```bash
   git am /path/to/patches/*.patch
   ```

## Validate

```bash
git log --oneline --decorate -n 20
git status --short --branch
```
