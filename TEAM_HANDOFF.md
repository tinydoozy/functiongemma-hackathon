# Team Handoff Notes (Frontend + Prompting + Tooling)

Use this file as the single place to summarize your changes so Andrew can cherry-pick or manually merge them into his branch.

## Recommended workflow

1. Keep coding changes in `main.py` (and any related files).
2. After each meaningful change, add a short note under **Change Log**.
3. Run local checks (`python -m py_compile ...`, `python benchmark.py` when possible).
4. Commit with a focused message.
5. Share commit hash + this file with Andrew.

## Change Log (append-only)

Copy/paste this block for each update:

```md
### YYYY-MM-DD HH:MM - <short title>
- Area: frontend | system prompt | tool descriptions | routing logic | misc
- Files touched:
  - `path/to/file.py`
- What changed:
  - ...
- Why:
  - ...
- Benchmark impact (if measured):
  - easy: ...
  - medium: ...
  - hard: ...
  - total score: ...
- Merge hints for Andrew:
  - Cherry-pick: `<commit_hash>`
  - If conflict: keep Andrew's ___, keep this branch's ___
```

## Suggested ownership split

- **You**
  - Prompt tuning (system prompt wording and tool guidance)
  - Tool descriptions/parameter clarity
  - Frontend-facing behavior and UX notes
- **Andrew**
  - Backend routing architecture
  - Performance optimization and final integration

## Practical merge options for Andrew

### Option A: Cherry-pick specific commits

```bash
git fetch origin
git checkout andrew-branch
git cherry-pick <commit_hash>
```

### Option B: Apply a patch file

From your branch:

```bash
git format-patch -1 <commit_hash>
```

From Andrew's branch:

```bash
git am <patch_file>
```

### Option C: Manual port with checklist

- Open your latest `TEAM_HANDOFF.md` entries.
- Apply file-by-file in this order:
  1. `main.py` logic changes
  2. tool definitions/prompt text
  3. benchmark or test adjustments
- Run `python benchmark.py` to confirm behavior.

## PR checklist (for your updates)

- [ ] `generate_hybrid` signature unchanged
- [ ] Output fields still include `function_calls`, `total_time_ms`, and `source`
- [ ] Notes added to **Change Log**
- [ ] Local checks run
- [ ] Commit hash shared with Andrew
