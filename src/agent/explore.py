"""Schema exploration: tables, columns, sample values, NULL detection."""
import logging
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ColumnInfo:
    name: str
    dtype: str
    sample_values: list[Any] = field(default_factory=list)
    has_nulls: bool = False


@dataclass
class TableInfo:
    name: str
    row_count: int
    columns: list[ColumnInfo] = field(default_factory=list)
    sample_rows: list[dict] = field(default_factory=list)


@dataclass
class SchemaInfo:
    db_path: str
    tables: list[TableInfo] = field(default_factory=list)

    def to_prompt_str(self) -> str:
        """Render schema as a compact, prompt-ready string."""
        lines = []
        for t in self.tables:
            lines.append(f"Table: {t.name} ({t.row_count} rows)")
            for c in t.columns:
                null_note = " [has NULLs]" if c.has_nulls else ""
                vals = ", ".join(repr(v) for v in c.sample_values[:6])
                # Quote names with spaces so the model copies them correctly
                display_name = f'"{c.name}"' if " " in c.name or "(" in c.name else c.name
                lines.append(f"  {display_name} {c.dtype}{null_note}  e.g. {vals}")
            if t.sample_rows:
                lines.append("  Sample rows:")
                for row in t.sample_rows[:3]:
                    lines.append(f"    {row}")
            lines.append("")
        return "\n".join(lines).rstrip()


def explore(
    db_path: str | Path,
    sample_rows: int = 3,
    sample_distinct: int = 10,
) -> SchemaInfo:
    """Return schema info including sample values and row counts for every table."""
    db_path = str(db_path)
    info = SchemaInfo(db_path=db_path)

    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    try:
        for table_name in _get_tables(con):
            tinfo = _explore_table(con, table_name, sample_rows, sample_distinct)
            info.tables.append(tinfo)
            logger.debug(
                "explore | table=%s cols=%d rows=%d",
                table_name, len(tinfo.columns), tinfo.row_count,
            )
    finally:
        con.close()

    return info


def _get_tables(con: sqlite3.Connection) -> list[str]:
    rows = con.execute(
        "SELECT name FROM sqlite_master "
        "WHERE type='table' AND name NOT LIKE 'sqlite_%' "
        "ORDER BY name"
    ).fetchall()
    return [r[0] for r in rows]


def _explore_table(
    con: sqlite3.Connection,
    name: str,
    sample_rows: int,
    sample_distinct: int,
) -> TableInfo:
    row_count: int = con.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0]
    pragma = con.execute(f'PRAGMA table_info("{name}")').fetchall()

    columns: list[ColumnInfo] = []
    for row in pragma:
        col_name: str = row[1]
        col_type: str = row[2] or "TEXT"

        null_count: int = con.execute(
            f'SELECT COUNT(*) FROM "{name}" WHERE "{col_name}" IS NULL'
        ).fetchone()[0]

        try:
            distinct_rows = con.execute(
                f'SELECT DISTINCT "{col_name}" FROM "{name}" '
                f'WHERE "{col_name}" IS NOT NULL LIMIT {sample_distinct}'
            ).fetchall()
            sample_values = [r[0] for r in distinct_rows]
        except Exception:
            sample_values = []

        columns.append(
            ColumnInfo(
                name=col_name,
                dtype=col_type,
                sample_values=sample_values,
                has_nulls=null_count > 0,
            )
        )

    try:
        raw_rows = con.execute(f'SELECT * FROM "{name}" LIMIT {sample_rows}').fetchall()
        sample_rows_data = [dict(r) for r in raw_rows]
    except Exception:
        sample_rows_data = []

    return TableInfo(
        name=name,
        row_count=row_count,
        columns=columns,
        sample_rows=sample_rows_data,
    )
