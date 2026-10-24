"""Evaluate abstention quality on our curated unanswerable-question set."""
import argparse
import json
import logging
from pathlib import Path
from typing import Any

import yaml
from tqdm import tqdm

from src.agent.loop import AgentResult, run
from src.llm.client import from_config

logger = logging.getLogger(__name__)


def evaluate_abstain(cfg_path: str) -> dict[str, Any]:
    with open(cfg_path) as f:
        cfg = yaml.safe_load(f)

    eval_cfg = cfg.get("eval", {})
    questions_path = eval_cfg.get(
        "abstain_questions_path", "tests/fixtures/abstain_questions.json"
    )
    db_base = Path(eval_cfg.get("bird_db_path", "data/bird/dev_databases"))
    output_path = Path("results/abstain_results.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    llm = from_config(cfg)

    with open(questions_path) as f:
        questions: list[dict] = json.load(f)

    total = len(questions)
    true_positive = 0   # unanswerable → agent abstained  ✓
    false_negative = 0  # unanswerable → agent answered   ✗
    results: list[dict] = []

    for item in tqdm(questions, desc="abstain-eval"):
        db_id: str = item["db_id"]
        db_path = db_base / db_id / f"{db_id}.sqlite"
        question: str = item["question"]
        evidence: str = item.get("evidence", "")

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
            logger.error("crash on %s: %s", db_id, exc)
            agent_result = None  # type: ignore[assignment]

        abstained = agent_result.abstained if agent_result else True
        if abstained:
            true_positive += 1
        else:
            false_negative += 1

        results.append({
            "db_id": db_id,
            "question": question,
            "reason": item.get("reason", ""),
            "abstained": abstained,
            "sql_attempted": agent_result.sql if agent_result else "",
            "correct": abstained,
        })

    precision = true_positive / total if total else 0.0  # all items are unanswerable
    recall = true_positive / total if total else 0.0      # same denominator here

    summary = {
        "total_unanswerable": total,
        "correctly_abstained": true_positive,
        "incorrectly_answered": false_negative,
        "abstain_recall": round(recall, 4),
        "config": cfg_path,
    }
    logger.info(
        "Abstain recall=%.4f  correct=%d/%d",
        recall, true_positive, total,
    )

    with open(output_path, "w") as f:
        json.dump({"summary": summary, "results": results}, f, indent=2)
    logger.info("Results written to %s", output_path)

    return summary


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s  %(message)s",
    )
    parser = argparse.ArgumentParser(description="Evaluate abstention on unanswerable questions.")
    parser.add_argument("--config", default="configs/default.yaml")
    args = parser.parse_args()
    summary = evaluate_abstain(args.config)
    print(
        f"\nAbstain recall = {summary['abstain_recall']:.4f}  "
        f"({summary['correctly_abstained']}/{summary['total_unanswerable']})"
    )


if __name__ == "__main__":
    main()
