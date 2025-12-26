---
name: Bug Report
about: Report a bug with structured investigation workflow
title: '[BUG] '
labels: 'bug, needs-investigation'
assignees: ''
---

## Bug Report Overview
**Bug Type**: [ ] Crash/Error [ ] Incorrect Output [ ] Performance [ ] CLI Interface [ ] Other: ___
**Severity**: [ ] Critical [ ] High [ ] Medium [ ] Low

---

## Problem Description
<!-- Provide a clear and concise description of the bug -->

### Expected vs Actual Behavior
**Expected**: [What should happen]
**Actual**: [What actually happens]
**Impact**: [How this affects users]

### Reproduction Steps
1. **Environment Setup**: [initial conditions]
2. **Command Executed**: `triagent [command] [arguments]`
3. **Trigger Action**: [specific action that causes bug]
4. **Observed Result**: [what happens]

**Reproducibility**: [ ] Always [ ] Sometimes [ ] Rarely [ ] Once

### Environment Context
- **OS**: [Windows 11, macOS 14.5, Ubuntu 22.04]
- **Python**: [3.11.x]
- **Triagent Version**: [0.1.0 or commit hash]
- **Install Method**: [pipx, pip, source]

### Error Evidence
```bash
# Command that fails
triagent [command]

# Complete error output
[Paste complete error message and stack trace here]
```

---

## Root Cause Analysis

### Initial Hypothesis
<!-- What do you think is causing this issue? -->

### Areas to Investigate
- [ ] **Input Validation**: Command parsing issues
- [ ] **API Integration**: Claude/Databricks connectivity
- [ ] **Error Handling**: Missing exception handling
- [ ] **CLI Interface**: Typer/prompt-toolkit issues
- [ ] **Dependencies**: Library version conflicts
- [ ] **Environment**: OS/Python version specific

---

## Resolution Validation

### Success Criteria
- [ ] Issue completely resolved for reported scenario
- [ ] No new bugs introduced by the fix
- [ ] Test coverage prevents regression
- [ ] Error handling is clear and helpful

---

## Related Work
- **Related Issues**: #
- **Similar Bugs**: #

## Priority Assessment
- [ ] **Critical**: Blocks core functionality
- [ ] **High**: Affects many users
- [ ] **Medium**: Affects some users
- [ ] **Low**: Minor issue with workarounds

---

## Additional Context
<!-- Any other context, workarounds, or relevant information -->
