"""Main agent loop: explore → generate → verify → (retry) → abstain/answer."""
import argparse
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml

from src.agent.abstain import should_abstain
from src.agent.explore import SchemaInfo, explore
from src.agent.generate import GenerateResult, generate
from src.agent.verify import VerifyResult, verify
from src.llm.client import LLMClient, from_config

logger = logging.getLogger(__name__)


@dataclass
class AgentResult:
    question: str
    db_id: str
    sql: str
    rows: list[dict]
    abstained: bool
    attempts: int
    total_latency_ms: float
    logs: list[str] = field(default_factory=list)

    def answer_text(self) -> str:
        if self.abstained:
            return "cannot answer"
        if not self.rows:
            return "(empty result)"
        if len(self.rows) == 1 and len(self.rows[0]) == 1:
            return str(next(iter(self.rows[0].values())))
        return str(self.rows)


def run(
    db_path: str | Path,
    question: str,
    evidence: str = "",
    db_id: str = "",
    cfg: Optional[dict] = None,
    llm: Optional[LLMClient] = None,
) -> AgentResult:
    """Run the agent for a single question and return a structured result."""
    t_start = time.monotonic()
    cfg = cfg or {}
    a = cfg.get("agent", {})
    max_retries: int = a.get("max_retries", 3)
    timeout: int = a.get("query_timeout", 30)
    row_limit: int = a.get("row_limit", 1000)
    sample_rows: int = a.get("sample_rows", 3)
    sample_distinct: int = a.get("sample_distinct", 10)
    null_threshold: float = a.get("null_ratio_threshold", 0.7)

    logs: list[str] = []

    schema: SchemaInfo = explore(db_path, sample_rows=sample_rows, sample_distinct=sample_distinct)
    logs.append(f"explored {len(schema.tables)} tables")

    if not schema.tables:
        return AgentResult(
            question=question, db_id=db_id, sql="", rows=[],
            abstained=True, attempts=0,
            total_latency_ms=(time.monotonic() - t_start) * 1000,
            logs=logs + ["abstained: database has no tables"],
        )

    error_feedback = ""
    last_gen: Optional[GenerateResult] = None
    last_ver: Optional[VerifyResult] = None

    for attempt in range(1, max_retries + 1):
        gen = generate(
            schema=schema,
            question=question,
            evidence=evidence,
            error_feedback=error_feedback,
            attempt=attempt,
            llm=llm,
        )
        last_gen = gen
        logs.append(f"attempt {attempt}: sql={gen.sql[:100]}")

        ver = verify(
            sql=gen.sql,
            db_path=db_path,
            timeout=timeout,
            row_limit=row_limit,
            null_ratio_threshold=null_threshold,
        )
        last_ver = ver
        logs.append(
            f"attempt {attempt}: ok={ver.ok} rows={ver.row_count} "
            f"error={ver.error!r} warnings={ver.warnings}"
        )

        if ver.ok:
            total_ms = (time.monotonic() - t_start) * 1000
            logger.info(
                "agent | DONE  attempt=%d rows=%d latency=%.0fms",
                attempt, ver.row_count, total_ms,
            )
            return AgentResult(
                question=question, db_id=db_id,
                sql=gen.sql, rows=ver.rows,
                abstained=False, attempts=attempt,
                total_latency_ms=total_ms, logs=logs,
            )

        error_feedback = ver.feedback
        logger.info("agent | retry %d/%d  feedback=%s", attempt, max_retries, error_feedback[:120])

    total_ms = (time.monotonic() - t_start) * 1000

    if should_abstain(last_ver, schema, question):
        logs.append("abstained: hard error after max retries")
        return AgentResult(
            question=question, db_id=db_id, sql="", rows=[],
            abstained=True, attempts=max_retries,
            total_latency_ms=total_ms, logs=logs,
        )

    # Return best-effort answer (e.g. query succeeds but returned 0 rows or high NULLs).
    logs.append("returning best-effort answer after max retries")
    return AgentResult(
        question=question, db_id=db_id,
        sql=last_gen.sql if last_gen else "",
        rows=last_ver.rows if last_ver else [],
        abstained=False, attempts=max_retries,
        total_latency_ms=total_ms, logs=logs,
    )


def _resolve_db_path(db_arg: str, cfg: dict) -> Path:
    """Accept either a file path or a db_id looked up in the config's db_path."""
    p = Path(db_arg)
    if p.exists():
        return p
    db_base = Path(cfg.get("eval", {}).get("bird_db_path", "data/bird/dev_databases"))
    candidate = db_base / db_arg / f"{db_arg}.sqlite"
    if candidate.exists():
        return candidate
    raise FileNotFoundError(
        f"Cannot resolve db {db_arg!r}. "
        f"Pass a path or a db_id resolvable under {db_base}."
    )


def _setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)-8s %(name)s  %(message)s",
        datefmt="%H:%M:%S",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the data-analyst agent on one question.")
    parser.add_argument("--db", required=True, help="db_id or path to .sqlite file")
    parser.add_argument("--question", required=True, help="Natural-language question")
    parser.add_argument("--evidence", default="", help="Domain knowledge hint (optional)")
    parser.add_argument("--config", default="configs/default.yaml", help="Config file")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    _setup_logging(args.verbose)

    with open(args.config) as f:
        cfg = yaml.safe_load(f)

    llm = from_config(cfg)
    db_path = _resolve_db_path(args.db, cfg)

    result = run(
        db_path=db_path,
        question=args.question,
        evidence=args.evidence,
        db_id=args.db,
        cfg=cfg,
        llm=llm,
    )

    print(f"\nQuestion : {result.question}")
    print(f"Answer   : {result.answer_text()}")
    print(f"SQL      : {result.sql}")
    print(f"Abstained: {result.abstained}  |  Attempts: {result.attempts}  |  "
          f"Latency: {result.total_latency_ms:.0f}ms")
    if args.verbose:
        print("\nTrace:")
        for line in result.logs:
            print(f"  {line}")


if __name__ == "__main__":
    main()
