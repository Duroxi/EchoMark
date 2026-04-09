import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import ThreadedConnectionPool
from contextlib import contextmanager
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/echomark")

_pool = None

def _get_pool():
    global _pool
    if _pool is None or _pool.closed:
        _pool = ThreadedConnectionPool(minconn=1, maxconn=10, dsn=DATABASE_URL)
    return _pool

@contextmanager
def get_db():
    pool = _get_pool()
    conn = pool.getconn()
    try:
        yield conn
    finally:
        pool.putconn(conn)

def execute_sql(sql: str, params: tuple = None, fetch_one=False, fetch_all=False):
    with get_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params)
            if fetch_one:
                result = cur.fetchone()
                conn.commit()
                return dict(result) if result else None
            if fetch_all:
                rows = [dict(row) for row in cur.fetchall()]
                conn.commit()
                return rows
            conn.commit()
            return cur.rowcount
