from src.agent.explore import explore


def test_table_count(sample_db):
    schema = explore(str(sample_db))
    assert len(schema.tables) == 2


def test_table_names(sample_db):
    schema = explore(str(sample_db))
    names = {t.name for t in schema.tables}
    assert names == {"schools", "districts"}


def test_row_counts(sample_db):
    schema = explore(str(sample_db))
    schools = next(t for t in schema.tables if t.name == "schools")
    assert schools.row_count == 5


def test_column_names(sample_db):
    schema = explore(str(sample_db))
    schools = next(t for t in schema.tables if t.name == "schools")
    col_names = [c.name for c in schools.columns]
    assert "name" in col_names
    assert "enrollment" in col_names
    assert "county" in col_names


def test_null_detection(sample_db):
    schema = explore(str(sample_db))
    schools = next(t for t in schema.tables if t.name == "schools")
    county = next(c for c in schools.columns if c.name == "county")
    assert county.has_nulls


def test_no_null_flag_on_clean_column(sample_db):
    schema = explore(str(sample_db))
    schools = next(t for t in schema.tables if t.name == "schools")
    id_col = next(c for c in schools.columns if c.name == "id")
    assert not id_col.has_nulls


def test_sample_values_present(sample_db):
    schema = explore(str(sample_db))
    schools = next(t for t in schema.tables if t.name == "schools")
    county = next(c for c in schools.columns if c.name == "county")
    # should include at least one real county value
    assert any(v in county.sample_values for v in ["Los Angeles", "San Francisco", "Oakland"])


def test_dirty_value_surfaced(sample_db):
    schema = explore(str(sample_db))
    schools = next(t for t in schema.tables if t.name == "schools")
    county = next(c for c in schools.columns if c.name == "county")
    assert "N/A" in county.sample_values


def test_prompt_str_contains_table(sample_db):
    schema = explore(str(sample_db))
    prompt = schema.to_prompt_str()
    assert "schools" in prompt
    assert "districts" in prompt
    assert "enrollment" in prompt


def test_sample_rows_returned(sample_db):
    schema = explore(str(sample_db))
    schools = next(t for t in schema.tables if t.name == "schools")
    assert len(schools.sample_rows) > 0
    assert "name" in schools.sample_rows[0]
