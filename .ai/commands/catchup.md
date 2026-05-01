---
name: catchup
description: >-
  Summarize what happened on the current branch since the developer's last
  contribution. Shows commits, authors, stats, and key changes.
argument-hint: "[developer email or name -- optional, defaults to local git user]"
---

# Commands - Catchup: Branch Activity Since Last Contribution

Produce a focused summary for a developer returning to a feature branch.

## Input

`$ARGUMENTS` -- optional identity of the returning developer:
- empty -> use `git config user.email`
- an email -> match commits by author email
- a name -> match commits by author name (case-insensitive)

## Workflow

### 1. Resolve Context

Run in parallel:
- `git rev-parse --abbrev-ref HEAD` -> current branch
- `git config user.email` and `git config user.name` -> default identity
- `git remote show origin | sed -n 's/.*HEAD branch: //p'` -> base branch (fallback: `master`)
- `git fetch --quiet` if a remote exists (skip silently on failure)

Abort with a clear message if HEAD is detached or on `master`.

### 2. Find the Developer's Last Commit

```bash
git log <base>..HEAD --author="<dev>" -n 1 --format="%H %ci %s"
```

- Found -> use as the **since** anchor
- Not found -> use `git merge-base HEAD <base>` as anchor; note "first time on this branch"

### 3. Gather Activity

Read-only git commands between the anchor and HEAD:

```bash
# Commits with authors
git log <anchor>..HEAD --format="%h|%an|%ae|%cr|%s" --no-merges

# Author breakdown
git shortlog -sne <anchor>..HEAD --no-merges

# Diff stats
git diff --stat <anchor>..HEAD

# Per-file churn
git diff --numstat <anchor>..HEAD
```

### 4. Synthesize

Group changes by theme:
- **Features added** -- new behavior
- **Refactors** -- structural changes
- **Bug fixes** -- what broke and was fixed
- **Tests / tooling / CI** -- brief notes
- **Requires attention** -- migrations, schema changes, config changes, dependency bumps, security-sensitive files

Reference specific files and commit SHAs.

### 5. Format Report

```markdown
## Catchup -- `<branch>` for <Dev Name>
**Base:** `<base>` | **Since:** <anchor> | **Generated:** <date>

### At a glance
- **Commits:** N (from M authors)
- **Files changed:** F (+A / -D lines)
- **Your last commit:** `<sha>` -- "<subject>" (<relative time>)

### Who changed what
| Author | Commits | Lines (+/-) |
|--------|---------|-------------|
| ...    | ...     | ...         |

### Themes
**Features**
- <bullet> -- `sha1234` (`path/to/file`)

**Refactors / Bug fixes / Tests**
- ...

### Requires your attention
- <change> -- `sha`, `path`

### Commit log
- `sha` -- *Author* -- <relative time> -- subject
```

## Notes

- **Read-only**: never run `git pull`, `git checkout`, or anything that mutates state. Only `git fetch --quiet` is allowed.
- Keep the report under 300 lines. Truncate long diffs.
- If no commits are in range, output "You're up to date -- nothing new on `<branch>` since `<anchor>`."
