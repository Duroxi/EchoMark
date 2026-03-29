import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/echomark")

@contextmanager
def get_db():
    """Get database connection."""
    conn = psycopg2.connect(DATABASE_URL)
    try:
        yield conn
    finally:
        conn.close()

def execute_sql(sql: str, params: tuple = None, fetch_one=False, fetch_all=False):
    """Execute SQL and optionally fetch results."""
    with get_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params)
            if fetch_one:
                return dict(cur.fetchone())
            if fetch_all:
                return [dict(row) for row in cur.fetchall()]
            conn.commit()
            return cur.rowcount