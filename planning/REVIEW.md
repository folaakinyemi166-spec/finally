# Review

## Findings

- High: `.claude/settings.json:2-15` adds a `Stop` hook that runs `codex exec "Review changes since last commit and write results to a file named planning/REVIEW.md"`. A nested Codex session launched from that command will read the same workspace config and can trigger the same hook again on exit, which creates a self-reinforcing loop. The same command is also duplicated in `Independent-reviewer/.claude-plugin/hooks/hooks.json:2-18`, so if both sources load you can get multiple review jobs from one stop event.

- High: `.claude-plugin/marketplace.json:8-12` points the plugin source at `./independent-reviewer`, but the actual directory in the tree is `Independent-reviewer/`. That relative path resolves to nothing on case-sensitive filesystems, so the plugin will not load.

- Medium: `.claude/settings.json:14-15` removes the previously enabled `frontend-design`, `context7`, and `playwright` plugins and replaces them with only `independent-reviewer@fola-tools`. That regresses the repo's developer tooling and drops the Playwright-backed testing support the project still expects.

- Medium: `planning/MASSIVE_API.md:271-273` says `massive_client.py` divides `last_trade.timestamp` by `1_000_000` to get seconds, but the backend code actually divides by `1000.0`, and the installed Massive SDK exposes `sip_timestamp` rather than `timestamp` for `LastTrade`. The document is therefore internally inconsistent and will steer future fixes in the wrong direction unless it is aligned with the real field/unit pair.

- Low: `.claude/commands/deply-changes.md:1` is misspelled and its body says `git hib`. If contributors are expected to use this command, rename it and fix the wording.

## Notes

- The `README.md` edits are internally consistent with the backend files already present.
