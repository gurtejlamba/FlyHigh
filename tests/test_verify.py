from src.agent.verify import verify


def test_valid_select(sample_db):
    r = verify("SELECT * FROM schools", str(sample_db))
    assert r.ok
    assert r.row_count == 5
    assert r.error == ""


def test_count_query(sample_db):
    r = verify("SELECT COUNT(*) AS n FROM schools", str(sample_db))
    assert r.ok
    assert r.row_count == 1
    assert r.rows[0]["n"] == 5


def test_filtered_query(sample_db):
    r = verify("SELECT * FROM schools WHERE county = 'Oakland'", str(sample_db))
    assert r.ok
    assert r.row_count == 1


def test_forbidden_insert(sample_db):
    r = verify(
        "INSERT INTO schools VALUES (6, 'test', 'X', 100, '2023')",
        str(sample_db),
    )
    assert not r.ok
    assert "Forbidden" in r.error


def test_forbidden_drop(sample_db):
    r = verify("DROP TABLE schools", str(sample_db))
    assert not r.ok
    assert "Forbidden" in r.error


def test_forbidden_update(sample_db):
    r = verify("UPDATE schools SET enrollment = 0", str(sample_db))
    assert not r.ok


def test_syntax_error(sample_db):
    r = verify("SELECT FROOOM schools", str(sample_db))
    assert not r.ok
    assert r.error != ""


def test_missing_table(sample_db):
    r = verify("SELECT * FROM nonexistent_table", str(sample_db))
    assert not r.ok
    assert "no such table" in r.error.lower()


def test_empty_result_triggers_warning(sample_db):
    r = verify("SELECT * FROM schools WHERE enrollment > 999999", str(sample_db))
    assert not r.ok
    assert r.row_count == 0
    assert any("0 rows" in w for w in r.warnings)


def test_empty_sql(sample_db):
    r = verify("", str(sample_db))
    assert not r.ok
    assert "Empty" in r.error


def test_high_null_ratio(sample_db):
    r = verify(
        "SELECT NULL AS a, NULL AS b, NULL AS c FROM schools",
        str(sample_db),
        null_ratio_threshold=0.5,
    )
    assert not r.ok
    assert r.null_ratio == 1.0
    assert any("NULL" in w for w in r.warnings)


def test_feedback_includes_error(sample_db):
    r = verify("SELECT FROOOM schools", str(sample_db))
    assert "SQL error" in r.feedback


def test_feedback_includes_warning(sample_db):
    r = verify("SELECT * FROM schools WHERE enrollment > 999999", str(sample_db))
    assert "0 rows" in r.feedback


def test_join_query(sample_db):
    r = verify(
        "SELECT s.name, d.budget FROM schools s "
        "JOIN districts d ON LOWER(s.county) = LOWER(d.county)",
        str(sample_db),
    )
    assert r.ok
    assert r.row_count > 0
