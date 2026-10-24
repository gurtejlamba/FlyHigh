from src.agent.abstain import _is_hard_error, should_abstain
from src.agent.explore import SchemaInfo
from src.agent.verify import VerifyResult


def _schema() -> SchemaInfo:
    return SchemaInfo(db_path="test.sqlite", tables=[])


# --- _is_hard_error ---

def test_hard_error_no_such_table():
    assert _is_hard_error("no such table: students")


def test_hard_error_no_such_column():
    assert _is_hard_error("table schools has no column named salary")


def test_hard_error_syntax():
    assert _is_hard_error("near 'FROOOM': syntax error")


def test_hard_error_ambiguous():
    assert _is_hard_error("ambiguous column name: id")


def test_not_hard_error_empty_result():
    assert not _is_hard_error("Query returned 0 rows")


def test_not_hard_error_timeout():
    assert not _is_hard_error("Query timed out after 30s")


def test_not_hard_error_null_ratio():
    assert not _is_hard_error("High NULL ratio (80%)")


# --- should_abstain ---

def test_abstain_on_none_verify():
    assert should_abstain(None, _schema(), "what is the average salary?")


def test_abstain_on_hard_error():
    ver = VerifyResult(ok=False, error="no such table: employees")
    assert should_abstain(ver, _schema(), "list all employees")


def test_no_abstain_on_empty_result():
    ver = VerifyResult(
        ok=False,
        warnings=["Query returned 0 rows — condition may be too restrictive"],
    )
    assert not should_abstain(ver, _schema(), "which schools had falling enrolment?")


def test_no_abstain_on_high_null_ratio():
    ver = VerifyResult(
        ok=False,
        null_ratio=0.8,
        warnings=["High NULL ratio (80%) — possible wrong column or JOIN mismatch"],
    )
    assert not should_abstain(ver, _schema(), "what is the average enrollment?")


def test_no_abstain_on_successful_verify():
    ver = VerifyResult(ok=True, rows=[{"n": 5}], row_count=1)
    assert not should_abstain(ver, _schema(), "how many schools?")


def test_abstain_on_syntax_error():
    ver = VerifyResult(ok=False, error="near 'FROOOM': syntax error")
    assert should_abstain(ver, _schema(), "anything")
