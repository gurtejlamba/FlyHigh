"""Evaluate the agent on the BIRD benchmark using Execution Accuracy (EX)."""
import argparse
import json
import logging
import sqlite3
import time
from pathlib import Path
from typing import Any

import yaml
from tqdm import tqdm

from src.agent.loop import AgentResult, run
from src.llm.client import from_config

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Execution helpers
# ---------------------------------------------------------------------------

def exec_sql(sql: str, db_path: str, timeout: int = 30) -> list[tuple] | str:
    """Return sorted list of row tuples, or an error string."""
    if not sql or not sql.strip():
        return "ERROR: empty SQL"
    try:
        con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        con.execute(f"PRAGMA busy_timeout = {timeout * 1000}")
        rows = con.execute(sql).fetchall()
        con.close()
        # None (NULL) is not orderable vs str/int — use a stable sort key
        def _sort_key(row):
            return tuple((0, "") if v is None else (1, str(v)) for v in row)
        return sorted((tuple(r) for r in rows), key=_sort_key)
    except Exception as exc:
        return f"ERROR: {exc}"


def _normalize(val):
    """Round floats to 4 decimal places so minor precision diffs don't fail."""
    if isinstance(val, float):
        return round(val, 4)
    return val


def _norm_rows(rows: list[tuple]) -> list[tuple]:
    def _sort_key(row):
        return tuple((0, "") if v is None else (1, str(v)) for v in row)
    return sorted((tuple(_normalize(v) for v in row) for row in rows), key=_sort_key)


def ex_match(pred_sql: str, gold_sql: str, db_path: str) -> bool:
    """True when predicted and gold SQL return the same result set."""
    if not pred_sql or not pred_sql.strip():
        return False
    pred = exec_sql(pred_sql, db_path)
    gold = exec_sql(gold_sql, db_path)
    if isinstance(pred, str) or isinstance(gold, str):
        return False
    return _norm_rows(pred) == _norm_rows(gold)


# ---------------------------------------------------------------------------
# Main evaluation loop
# ---------------------------------------------------------------------------

def evaluate(cfg_path: str, split: str = "dev", limit: int | None = None) -> dict[str, Any]:
    with open(cfg_path) as f:
        cfg = yaml.safe_load(f)

    eval_cfg = cfg.get("eval", {})
    questions_path = eval_cfg.get(f"bird_{split}_path", f"data/bird/{split}.json")
    db_base = Path(eval_cfg.get(
        "bird_db_path" if split == "dev" else "bird_test_db_path",
        f"data/bird/{split}_databases",
    ))
    output_path = Path(eval_cfg.get("output_path", f"results/{split}_results.json"))
    output_path.parent.mkdir(parents=True, exist_ok=True)

    llm = from_config(cfg)

    with open(questions_path) as f:
        questions: list[dict] = json.load(f)

    if limit:
        questions = questions[:limit]

    total = len(questions)
    correct = 0
    abstained = 0
    results: list[dict] = []

    for item in tqdm(questions, desc=f"eval/{split}"):
        db_id: str = item["db_id"]
        db_path = db_base / db_id / f"{db_id}.sqlite"
        question: str = item["question"]
        evidence: str = item.get("evidence", "")
        gold_sql: str = item.get("SQL", "")

        t0 = time.monotonic()
        try:
            agent_result: AgentResult = run(
                db_path=db_path,
                question=question,
                evidence=evidence,
                db_id=db_id,
                cfg=cfg,
                llm=llm,
            )
        except Exception as exc:
            logger.error("agent crash on %s: %s", item.get("question_id"), exc)
            agent_result = None  # type: ignore[assignment]

        latency_ms = (time.monotonic() - t0) * 1000
        pred_sql = agent_result.sql if agent_result else ""
        abstained_flag = agent_result.abstained if agent_result else True

        if abstained_flag:
            abstained += 1

        match = ex_match(pred_sql, gold_sql, str(db_path)) if gold_sql else False
        if match:
            correct += 1

        results.append({
            "question_id": item.get("question_id"),
            "db_id": db_id,
            "question": question,
            "gold_sql": gold_sql,
            "pred_sql": pred_sql,
            "abstained": abstained_flag,
            "ex_match": match,
            "latency_ms": round(latency_ms, 1),
            "difficulty": item.get("difficulty", "unknown"),
            "attempts": agent_result.attempts if agent_result else 0,
        })

    ex = correct / total if total else 0.0
    summary = {
        "split": split,
        "total": total,
        "correct": correct,
        "abstained": abstained,
        "ex": round(ex, 4),
        "config": cfg_path,
    }
    logger.info(
        "EX=%.4f  correct=%d/%d  abstained=%d",
        ex, correct, total, abstained,
    )

    with open(output_path, "w") as f:
        json.dump({"summary": summary, "results": results}, f, indent=2)
    logger.info("Results written to %s", output_path)

    _print_failure_breakdown(results)
    return summary


def _print_failure_breakdown(results: list[dict]) -> None:
    """Log a simple difficulty breakdown of failures."""
    from collections import Counter
    failures = [r for r in results if not r["ex_match"] and not r["abstained"]]
    by_difficulty = Counter(r["difficulty"] for r in failures)
    logger.info("Failure breakdown by difficulty: %s", dict(by_difficulty))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s  %(message)s",
    )
    parser = argparse.ArgumentParser(description="BIRD execution-accuracy evaluation.")
    parser.add_argument("--config", default="configs/default.yaml")
    parser.add_argument("--split", default="dev", choices=["dev", "test"])
    parser.add_argument("--limit", type=int, default=None, help="Evaluate only the first N items")
    args = parser.parse_args()
    summary = evaluate(args.config, args.split, args.limit)
    print(f"\nEX = {summary['ex']:.4f}  ({summary['correct']}/{summary['total']})")


if __name__ == "__main__":
    main()
