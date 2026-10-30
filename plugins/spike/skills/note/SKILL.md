---
name: note
description: Use when the operator wants a sentence appended to the open spike's log, or says "note this".
argument-hint: <text>
---

# /spike:note

Append to the current direction's log, verbatim:

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/spike.py" note "$ARGUMENTS"
```

Reply with one word. If the operator's text is a question for later rather than a note, use `question` instead of `note`; if it is a decision ("record this"), use `decide --by operator`.
