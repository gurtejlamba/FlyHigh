"""SQL generation: builds a prompt and calls the LLM, then extracts the SQL."""
import logging
import re
from dataclasses import dataclass

from src.agent.explore import SchemaInfo
from src.llm.client import LLMClient, LLMResponse

logger = logging.getLogger(__name__)

_SYSTEM = """\
You are an expert SQLite analyst. Given a database schema and a natural-language question, \
write a single SQL SELECT query that answers the question exactly.

RULES (strictly enforced):
1. Output ONLY the raw SQL query. No explanation, no markdown fences, no extra text.
2. Use only SELECT. Never write INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, or PRAGMA assignments.
3. SQLite only — use SQLite-compatible syntax. Window functions (RANK() OVER, ROW_NUMBER() OVER, \
DENSE_RANK() OVER) ARE supported in SQLite 3.25+.
4. CRITICAL — use ONLY the exact table and column names listed in the schema.
   Never invent or guess names. Check the Available Tables section carefully before writing any JOIN.
5. Table aliases: `JOIN schools AS s` means alias `s` refers to `schools` only.
   Never access a column via an alias that belongs to a different table.
6. Column names with spaces or special characters MUST be double-quoted: "Percent (%) Eligible Free (K-12)".
7. Integer division truncates in SQLite. When computing a rate, percentage, or ratio, always cast:
   CAST(numerator AS REAL) / denominator
8. Do NOT add extra WHERE filters for aggregation-level indicator columns (e.g., do not add a
   filter like `col = 'some_level'` on columns that weren't mentioned in the question or evidence).
   These silent extra filters drop rows and produce wrong results.
9. Dirty data: columns may contain "N/A", "", or NULL. Exclude them only when filtering on that
   column: col NOT IN ('N/A', '') AND col IS NOT NULL
10. Case-insensitive matching: LOWER(col) = LOWER('value').
11. ALWAYS use ORDER BY col DESC LIMIT 1 (not WHERE col = (SELECT MAX(col))) when finding the row
    with the highest/lowest value — the MAX subquery pattern returns 0 rows if that extreme row
    is excluded by a JOIN or WHERE condition.
    BAD:  WHERE AvgScrMath = (SELECT MAX(AvgScrMath) FROM satscores)
    GOOD: ORDER BY AvgScrMath DESC LIMIT 1
12. When a question says "rank" or "ranking", use the RANK() OVER window function, NOT GROUP BY.
    Example: RANK() OVER (ORDER BY score DESC) AS rank
    Do NOT use AVG() or GROUP BY to answer ranking questions.
13. Prefer explicit JOINs over subqueries; qualify all column references with table aliases.
14. Return ONLY the columns the question explicitly asks for. Do not add extra indicator/flag
    columns to SELECT unless specifically requested.
15. Start your response directly with SELECT or WITH. No preamble, no explanation.
"""


@dataclass
class GenerateResult:
    sql: str
    raw_response: str
    prompt_tokens: int
    completion_tokens: int
    latency_ms: float


def generate(
    schema: SchemaInfo,
    question: str,
    evidence: str = "",
    error_feedback: str = "",
    attempt: int = 1,
    llm: LLMClient = None,
) -> GenerateResult:
    """Generate SQL for *question* given *schema*. Pass *error_feedback* on retries."""
    prompt = _build_prompt(schema, question, evidence, error_feedback, attempt)
    logger.info("generate | attempt=%d  q=%s", attempt, question[:100])
    logger.debug("prompt:\n%s", prompt)

    resp: LLMResponse = llm.generate(prompt, system=_SYSTEM)
    sql = _extract_sql(resp.text)
    logger.info("generate | sql=%s", sql[:140])

    return GenerateResult(
        sql=sql,
        raw_response=resp.text,
        prompt_tokens=resp.prompt_tokens,
        completion_tokens=resp.completion_tokens,
        latency_ms=resp.latency_ms,
    )


_MAX_SCHEMA_CHARS = 5000


def _build_prompt(
    schema: SchemaInfo,
    question: str,
    evidence: str,
    error_feedback: str,
    attempt: int,
) -> str:
    table_names = ", ".join(t.name for t in schema.tables)

    # Compact column list — always shown, never truncated
    col_summary_lines = []
    for t in schema.tables:
        cols = ", ".join(c.name for c in t.columns)
        col_summary_lines.append(f"  {t.name}: {cols}")
    col_summary = "\n".join(col_summary_lines)

    schema_str = schema.to_prompt_str()
    if len(schema_str) > _MAX_SCHEMA_CHARS:
        schema_str = schema_str[:_MAX_SCHEMA_CHARS] + "\n  ... (truncated)"

    parts = [
        f"### Available Tables (use ONLY these exact names)\n{col_summary}\n",
        f"### Full Schema\n{schema_str}",
    ]

    if evidence:
        parts.append(f"\n### Domain Knowledge / Hints\n{evidence}")

    parts.append(f"\n### Question\n{question}")

    if error_feedback and attempt > 1:
        parts.append(
            f"\n### Previous Attempt Failed\n"
            f"{error_feedback}\n"
            f"Fix the query. Column names containing spaces or parentheses MUST be "
            f'double-quoted, e.g. "Percent (%) Eligible Free (K-12)". '
            f"Use ONLY these tables: {table_names}"
        )

    # Reminder at the bottom — last thing the model reads before generating
    parts.append(
        f"\n### REMINDER\n"
        f"Valid table names: {table_names}\n"
        f"Output ONLY the SQL query starting with SELECT or WITH."
    )
    return "\n".join(parts)


def _extract_sql(text: str) -> str:
    """Strip markdown fences and leading prose; return the SQL statement."""
    text = text.strip()

    # ```sql ... ``` or ``` ... ```
    fence = re.search(r"```(?:sql)?\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if fence:
        return fence.group(1).strip()

    # SELECT / WITH at start of a line
    m = re.search(r"^((?:SELECT|WITH)\b.+)", text, re.DOTALL | re.IGNORECASE | re.MULTILINE)
    if m:
        return m.group(1).strip()

    return text
