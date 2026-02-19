"""
Create the DataBridge database and user in PostgreSQL.

Usage (from the backend/ directory):
    python -m scripts.create_db

Requires psycopg2 and superuser access to PostgreSQL.
"""
from __future__ import annotations

import sys

DB_NAME = "databridge_db"
DB_USER = "databridge_user"
DB_PASSWORD = "change_me_in_production"
PG_HOST = "localhost"
PG_PORT = 5432


def main() -> None:
    try:
        import psycopg2
        from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
    except ImportError:
        print("psycopg2 not installed. Install with: pip install psycopg2-binary")
        sys.exit(1)

    pg_password = input("Enter PostgreSQL superuser (postgres) password: ").strip()
    if not pg_password:
        print("Password required.")
        sys.exit(1)

    conn = psycopg2.connect(
        host=PG_HOST,
        port=PG_PORT,
        user="postgres",
        password=pg_password,
        dbname="postgres",
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()

    # Create role if not exists
    cur.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (DB_USER,))
    if cur.fetchone() is None:
        cur.execute(
            f"CREATE ROLE {DB_USER} WITH LOGIN PASSWORD %s",
            (DB_PASSWORD,),
        )
        print(f"Created role: {DB_USER}")
    else:
        print(f"Role already exists: {DB_USER}")

    # Create database if not exists
    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DB_NAME,))
    if cur.fetchone() is None:
        cur.execute(f"CREATE DATABASE {DB_NAME} OWNER {DB_USER}")
        print(f"Created database: {DB_NAME}")
    else:
        print(f"Database already exists: {DB_NAME}")

    # Grant privileges
    cur.execute(f"GRANT ALL PRIVILEGES ON DATABASE {DB_NAME} TO {DB_USER}")
    print(f"Granted all privileges on {DB_NAME} to {DB_USER}")

    # Connect to the new DB and grant schema access
    cur.close()
    conn.close()

    conn2 = psycopg2.connect(
        host=PG_HOST,
        port=PG_PORT,
        user="postgres",
        password=pg_password,
        dbname=DB_NAME,
    )
    conn2.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur2 = conn2.cursor()
    cur2.execute(f"GRANT ALL ON SCHEMA public TO {DB_USER}")
    cur2.execute(f"ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO {DB_USER}")
    cur2.execute(f"ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO {DB_USER}")
    print(f"Granted schema privileges to {DB_USER}")
    cur2.close()
    conn2.close()

    print()
    print("Database setup complete!")
    print(f"  DATABASE_URL=postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{PG_HOST}:{PG_PORT}/{DB_NAME}")
    print()
    print("Update your .env file with the above URL, then run:")
    print("  cd backend && alembic upgrade head")


if __name__ == "__main__":
    main()
