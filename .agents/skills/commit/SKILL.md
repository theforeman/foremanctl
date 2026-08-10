---
name: commit
description: >-
  Write a git commit message following the seven rules of a great commit message.
  Use this skill whenever you are asked to commit changes.
---

# Commit

Write a git commit message that follows the seven rules from
[How to Write a Git Commit Message](https://cbea.ms/git-commit/).

## Workflow

1. Examine staged and unstaged changes
2. Review recent commit history for style context
3. Draft a commit message applying all seven rules
4. Stage relevant files and commit

### 1. Examine changes

```shell
git status
git diff --staged
git diff
```

Review every changed file to understand *what* changed and *why*.

### 2. Review recent commits

```shell
git log --oneline -10
```

Note any project conventions (e.g. prefixes, issue references) used alongside the rules below.

### 3. Draft the commit message

Apply all seven rules when writing the message:

#### Rule 1 — Separate subject from body with a blank line

The first line is the subject. If the commit needs explanation, leave one blank line then write the body. Tools like `git log --oneline`, `git shortlog`, and `git format-patch` depend on this separation.

Simple, self-explanatory changes need only a subject — no body required.

#### Rule 2 — Limit the subject line to 50 characters

Aim for 50 characters. Treat 72 as the hard limit. If you struggle to fit the summary, the commit may bundle too many changes — consider whether it should be split.

#### Rule 3 — Capitalize the subject line

Begin the subject with a capital letter.

Good: `Refactor deployment playbook for clarity`
Bad: `refactor deployment playbook for clarity`

#### Rule 4 — Do not end the subject line with a period

Trailing punctuation wastes space and adds nothing.

Good: `Fix TLS certificate path lookup`
Bad: `Fix TLS certificate path lookup.`

#### Rule 5 — Use the imperative mood in the subject line

Write as if completing the sentence: *"If applied, this commit will …"*

Good subjects:
- Add health-check role for Candlepin
- Remove deprecated Puppet integration
- Update tuning defaults for large deployments

Bad subjects:
- ~~Added health-check role for Candlepin~~
- ~~Removes deprecated Puppet integration~~
- ~~Updating tuning defaults for large deployments~~

The imperative requirement applies to the subject only. The body may use any tense.

#### Rule 6 — Wrap the body at 72 characters

Hard-wrap every line in the body at 72 characters so text remains readable in terminals and `git log` output.

#### Rule 7 — Use the body to explain *what* and *why*, not *how*

The diff shows *how*. Use the body to explain:
- What problem this commit solves
- Why this approach was chosen
- Any non-obvious side effects or consequences

Omit the body when the subject alone makes the change self-evident.

### 4. Stage and commit

Stage only the files relevant to this change — do not use `git add -A` or `git add .` unless every changed file belongs in this commit. Avoid staging files that may contain secrets.

Pass the message via a heredoc to preserve formatting:

```shell
git commit -m "$(cat <<'EOF'
Subject line here

Body text here, wrapped at 72 characters. Explain what changed
and why, not how.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)"
```

### Checklist before committing

- [ ] Subject is under 50 characters (72 max)
- [ ] Subject starts with a capital letter
- [ ] Subject has no trailing period
- [ ] Subject uses imperative mood ("Add", "Fix", "Remove", not "Added", "Fixes", "Removing")
- [ ] Subject and body are separated by a blank line (if body is present)
- [ ] Body lines wrap at 72 characters
- [ ] Body explains *what* and *why*, not *how*
- [ ] No secrets or credentials in staged files
