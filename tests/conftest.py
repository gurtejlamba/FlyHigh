import sqlite3

import pytest


@pytest.fixture
def sample_db(tmp_path):
    """Small SQLite database with realistic dirty data for unit tests."""
    db_path = tmp_path / "test.sqlite"
    con = sqlite3.connect(str(db_path))
    con.executescript("""
        CREATE TABLE schools (
            id        INTEGER PRIMARY KEY,
            name      TEXT,
            county    TEXT,
            enrollment INTEGER,
            school_year TEXT
        );
        INSERT INTO schools VALUES
            (1, 'Lincoln High',  'Los Angeles',   500,  '2022-23'),
            (2, 'Washington',    'San Francisco', 1200,  '2022-23'),
            (3, 'Jefferson',     NULL,               0,  'N/A'),
            (4, 'Roosevelt',     'Oakland',        300,  '2022-23'),
            (5, 'Adams',         'N/A',           NULL,  '2021-22');

        CREATE TABLE districts (
            id      INTEGER PRIMARY KEY,
            name    TEXT,
            county  TEXT,
            budget  REAL
        );
        INSERT INTO districts VALUES
            (1, 'LA Unified',  'Los Angeles',   1000000.0),
            (2, 'SFUSD',       'San Francisco',  500000.0),
            (3, 'Oakland USD', 'Oakland',        300000.0);
    """)
    con.commit()
    con.close()
    return db_path
