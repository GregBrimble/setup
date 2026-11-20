---
name: tobi-try
description: Manage experiment directories, repository clones, GitHub PRs, and detached worktrees with tobi/try. Use when the user requests a try workspace or mentions tobi/try.
---

# tobi/try

Greg's experiment root is `~/Developer/tries`. Check `try --help` for the
installed interface; pass the absolute root explicitly in noninteractive calls.

```sh
try exec --path "$HOME/Developer/tries" clone https://github.com/owner/repo.git
try exec --path "$HOME/Developer/tries" clone https://github.com/owner/repo/pull/123
try exec --path "$HOME/Developer/tries" worktree /absolute/source/repo experiment-name
```

The executable prints shell code. Capture it, check the exit status and intended
operations, then execute it without changing its quoting. Use the resulting
absolute directory as the working directory for subsequent calls.

For a plain experiment, run `try exec --path <root> . <name>` from outside a Git
repository; inside one it creates a worktree. Explicit clone names are used
verbatim, without a date prefix. Use the user's local date when naming tries.

PRs and worktrees start detached; worktrees omit uncommitted source changes.
Creation can suppress Git errors: verify the destination is its own Git root
and that a worktree appears in `git worktree list` before reporting success.

For discovery, inspect immediate directories under the root. `try query` is an
interactive selector. Use Git's worktree operations when removing worktrees.
