"""SQL verification: execute safely, run sanity checks, return structured result."""
import logging
import re
import sqlite3
import threading
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

# Statements that must never appear at the top level of the query.
_FORBIDDEN_RE = re.compile(
    r"^\s*(?:INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|REPLACE|TRUNCATE|ATTACH|DETACH)\b"
    r"|PRAGMA\s+\w+\s*=",
    re.IGNORECASE,
)


@dataclass
class VerifyResult:
    ok: bool
    rows: list[dict] = field(default_factory=list)
    row_count: int = 0
    error: str = ""
    warnings: list[str] = field(default_factory=list)
    null_ratio: float = 0.0

    @property
    def feedback(self) -> str:
        """Human-readable description of what went wrong, for use in repair prompts."""
        parts = []
        if self.error:
            parts.append(f"SQL error: {self.error}")
        parts.extend(self.warnings)
        return " | ".join(parts) if parts else ""


def verify(
    sql: str,
    db_path: str | Path,
    timeout: int = 30,
    row_limit: int = 1000,
    null_ratio_threshold: float = 0.7,
) -> VerifyResult:
    """Execute *sql* against *db_path* (read-only) and run sanity checks."""
    if not sql or not sql.strip():
        return VerifyResult(ok=False, error="Empty SQL")

    if _FORBIDDEN_RE.search(sql):
        return VerifyResult(ok=False, error="Forbidden statement (only SELECT is allowed)")

    rows_out: list = []
    err_out: list[str] = []
    con_holder: list[sqlite3.Connection] = []

    def _run() -> None:
        try:
            con = sqlite3.connect(f"file:{str(db_path)}?mode=ro", uri=True)
            con_holder.append(con)
            con.row_factory = sqlite3.Row
            cur = con.execute(sql)
            rows_out.extend(cur.fetchmany(row_limit))
            con.close()
        except Exception as exc:
            err_out.append(str(exc))

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    t.join(timeout)

    if t.is_alive():
        if con_holder:
            try:
                con_holder[0].interrupt()
            except Exception:
                pass
        t.join(2)
        return VerifyResult(ok=False, error=f"Query timed out after {timeout}s")

    if err_out:
        return VerifyResult(ok=False, error=err_out[0])

    rows_as_dicts = [dict(r) for r in rows_out]
    warnings: list[str] = []

    if not rows_as_dicts:
        warnings.append(
            "Query returned 0 rows — condition may be too restrictive or reference wrong column"
        )

    null_ratio = 0.0
    if rows_as_dicts:
        total = sum(len(r) for r in rows_as_dicts)
        nulls = sum(1 for r in rows_as_dicts for v in r.values() if v is None)
        null_ratio = nulls / total if total else 0.0
        if null_ratio > null_ratio_threshold:
            warnings.append(
                f"High NULL ratio ({null_ratio:.0%}) — possible wrong column or JOIN mismatch"
            )

    return VerifyResult(
        ok=len(warnings) == 0,
        rows=rows_as_dicts,
        row_count=len(rows_as_dicts),
        warnings=warnings,
        null_ratio=null_ratio,
    )
