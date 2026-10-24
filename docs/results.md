# Evaluation Results

Record every eval run here. Change one thing at a time; log EX before and after.

## Format

| Date | Model | Config | Split | EX | Abstain P | Abstain R | Notes |
|------|-------|--------|-------|----|-----------|-----------|-------|
| — | — | — | dev | — | — | — | baseline (not yet run) |

## Definitions

- **EX**: Execution Accuracy — fraction of questions where predicted SQL returns the same result set as gold SQL.
- **Abstain P**: Precision of abstention on our unanswerable-question set (fraction of abstentions that were correct).
- **Abstain R**: Recall of abstention (fraction of unanswerable questions where the agent abstained).

## Failure analysis template

| Category | Count | % of errors | Example question |
|----------|-------|-------------|-----------------|
| Wrong table selected | — | — | — |
| Dirty value not handled | — | — | — |
| Missing domain knowledge | — | — | — |
| Bad SQL / syntax | — | — | — |
| Correct abstention | — | — | — |
| Wrong abstention | — | — | — |

## Demo scenarios

1. **Self-repair**: agent produces wrong SQL on attempt 1 (e.g., joins wrong table), verify flags it, attempt 2 succeeds.
2. **Correct refusal**: question asks about data not in the schema; agent abstains instead of guessing.
3. **Dirty data**: column contains "N/A" strings; agent filters them before aggregating.
