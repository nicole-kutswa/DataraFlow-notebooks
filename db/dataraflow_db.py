"""Read-only database access for DataRaflow interns."""

import os
from urllib.parse import quote_plus

import pandas as pd
import pymssql
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

_engine = None


def get_engine():
    """Return a cached read-only SQLAlchemy engine for the cohort database."""
    global _engine

    if _engine is None:
        user = os.environ["SQL_READONLY_USERNAME"]
        pwd = quote_plus(os.environ["SQL_READONLY_PASSWORD"])
        host = os.environ["SQL_SERVER_NAME"]
        db = os.environ["SQL_SERVER_DATABASE"]

        _engine = create_engine(
            f"mssql+pymssql://{user}:{pwd}@{host}:1433/{db}?tds_version=7.4",
            connect_args={
                "login_timeout": 15,
                "timeout": 30,
            },
        )

    return _engine


def get_connection():
    """Open a raw read-only pymssql connection (for manual cursor use)."""
    return pymssql.connect(
        server=os.environ["SQL_SERVER_NAME"],
        user=os.environ["SQL_READONLY_USERNAME"],
        password=os.environ["SQL_READONLY_PASSWORD"],
        database=os.environ["SQL_SERVER_DATABASE"],
        port=1433,
        tds_version="7.4",
        login_timeout=15,
        timeout=30,
    )


def run_query(sql: str) -> pd.DataFrame:
    """Run a SELECT query and return the result as a pandas DataFrame."""
    return pd.read_sql(sql, get_engine())
