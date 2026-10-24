"""Abstention logic: decide when to say 'cannot answer' instead of guessing."""
import logging
import re
from typing import Optional

from src.agent.explore import SchemaInfo
from src.agent.verify import VerifyResult

logger = logging.getLogger(__name__)

# Errors that indicate the question genuinely cannot be answered with this schema.
_HARD_ERROR_RE = re.compile(
    r"no such table|no such column|has no column named|syntax error|ambiguous column name",
    re.IGNORECASE,
)


def should_abstain(
    ver: Optional[VerifyResult],
    schema: SchemaInfo,
    question: str,
) -> bool:
    """Return True when the agent should say 'cannot answer'.

    Conservative: only abstain on hard SQL errors after all retries.  Empty
    results might be correct (the real answer is zero rows), so we do not
    abstain on those alone.
    """
    if ver is None:
        logger.info("abstain: no verify result")
        return True

    if ver.error and _is_hard_error(ver.error):
        logger.info("abstain: hard SQL error — %s", ver.error)
        return True

    return False


def _is_hard_error(error: str) -> bool:
    """True when the error signals that no valid query can be written."""
    return bool(_HARD_ERROR_RE.search(error))
