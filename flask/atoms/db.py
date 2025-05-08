import os
import psycopg2
from psycopg2.errors import UniqueViolation, ForeignKeyViolation
from dotenv import load_dotenv

load_dotenv()

def get_db_config():
    return {
        "host": os.getenv("POSTGRESQL_HOST"),
        "database": os.getenv("POSTGRESQL_DATABASE"),
        "user": os.getenv("POSTGRESQL_USER"),
        "password": os.getenv("POSTGRESQL_PASSWORD"),
        "port": os.getenv("POSTGRESQL_PORT", 5432)
    }

def get_conn():
    """Return a psycopg2 connection using env variables."""
    return psycopg2.connect(**get_db_config())

def run_query(query, params=None, fetch_one=False, fetch_all=False):
    """
    Execute a query safely with automatic connection and cursor handling.

    - query: SQL query string
    - params: tuple of parameters
    - fetch_one: return one result (dict)
    - fetch_all: return all results (list of dicts)
    """
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params or ())

                if fetch_one:
                    row = cur.fetchone()
                    if not row:
                        return None
                    cols = [desc[0] for desc in cur.description]
                    return dict(zip(cols, row))

                if fetch_all:
                    rows = cur.fetchall()
                    cols = [desc[0] for desc in cur.description]
                    return [dict(zip(cols, r)) for r in rows]

                conn.commit()
                return None
    except UniqueViolation:
        raise ValueError(f"Already exists")
    except ForeignKeyViolation:
        raise ValueError(f"Invalid foreign key")
    except Exception as e:
        raise RuntimeError(f"Failed to insert: {str(e)}")
