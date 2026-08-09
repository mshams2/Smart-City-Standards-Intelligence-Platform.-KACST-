from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Iterator

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = BASE_DIR / "data" / "smart_city.db"


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(
        DATABASE_PATH,
        timeout=30,
        check_same_thread=False,
    )

    connection.row_factory = sqlite3.Row

    try:
        connection.execute("PRAGMA foreign_keys = ON;")
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def initialize_database() -> None:
    query = """
    CREATE TABLE IF NOT EXISTS project_checker_submissions (
        submission_id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_name TEXT NOT NULL,
        domain TEXT NOT NULL,
        project_type TEXT,
        technology_used TEXT,
        data_sources TEXT,
        target_users TEXT,
        expected_impact TEXT,
        current_status TEXT,
        available_evidence TEXT,
        submitted_at TEXT NOT NULL
    );
    """

    with get_connection() as connection:
        connection.execute(query)

        existing_columns = {
            row["name"]
            for row in connection.execute(
                "PRAGMA table_info(project_checker_submissions);"
            )
        }
        if "project_type" not in existing_columns:
            connection.execute(
                "ALTER TABLE project_checker_submissions ADD COLUMN project_type TEXT;"
            )
        if "updated_at" not in existing_columns:
            connection.execute(
                "ALTER TABLE project_checker_submissions ADD COLUMN updated_at TEXT;"
            )


def save_project_submission(
    project_name: str,
    domain: str,
    project_type: str,
    technology_used: str,
    data_sources: str,
    target_users: str,
    expected_impact: str,
    current_status: str,
    available_evidence: str,
) -> int:
    initialize_database()

    query = """
    INSERT INTO project_checker_submissions (
        project_name,
        domain,
        project_type,
        technology_used,
        data_sources,
        target_users,
        expected_impact,
        current_status,
        available_evidence,
        submitted_at,
        updated_at
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """

    submitted_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    values = (
        project_name.strip(),
        domain.strip(),
        project_type.strip(),
        technology_used.strip(),
        data_sources.strip(),
        target_users.strip(),
        expected_impact.strip(),
        current_status.strip(),
        available_evidence.strip(),
        submitted_at,
        submitted_at,
    )

    with get_connection() as connection:
        cursor = connection.execute(query, values)
        return int(cursor.lastrowid)


def get_project_submissions() -> pd.DataFrame:
    initialize_database()

    query = """
    SELECT
        submission_id,
        project_name,
        domain,
        project_type,
        technology_used,
        data_sources,
        target_users,
        expected_impact,
        current_status,
        available_evidence,
        submitted_at
    FROM project_checker_submissions
    ORDER BY submission_id DESC;
    """

    with get_connection() as connection:
        return pd.read_sql_query(query, connection)

def delete_project_submission(submission_id: int) -> bool:
    initialize_database()

    query = """
    DELETE FROM project_checker_submissions
    WHERE submission_id = ?;
    """

    with get_connection() as connection:
        cursor = connection.execute(
            query,
            (submission_id,),
        )

        return cursor.rowcount > 0