import os
import time
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

# -----------------------------------------------------------
#  CONFIG
# -----------------------------------------------------------

DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://airbnb_user:airbnb_password@postgres:5432/airbnb_db"
)

CSV_FILES = {
    "hosts": ["RAW_HOST.csv"],
    "listings": ["RAW_LISTING.csv"],
    "reviews": ["RAW_REVIEWS.csv"],
}

SEARCH_PATHS = [
    "/data",
    "/mnt/data",     # for uploaded ChatGPT files
]

TARGET_SCHEMA = "raw"


# -----------------------------------------------------------
#  HELPER FUNCTIONS
# -----------------------------------------------------------

def find_file(filename: str):
    """Search for a CSV file in /data or /mnt/data."""
    for path in SEARCH_PATHS:
        candidate = os.path.join(path, filename)
        if os.path.exists(candidate):
            print(f"✓ Found {filename} at {candidate}")
            return candidate
    raise FileNotFoundError(f"CSV file {filename} not found in {SEARCH_PATHS}")


def wait_for_db(engine, timeout_seconds=180):
    """Wait until PostgreSQL is ready to accept connections."""
    print("Waiting for PostgreSQL to be ready...")
    start = time.time()

    while True:
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                print("✓ PostgreSQL is ready.")
                return

        except OperationalError as e:
            if time.time() - start > timeout_seconds:
                raise TimeoutError("PostgreSQL did not become ready in time") from e
            print("Postgres not ready yet… retrying in 2s")
            time.sleep(2)


def load_csv_to_db(engine, filename, table_name):
    """Load a CSV into PostgreSQL under raw.<table>."""
    filepath = find_file(filename)
    print(f"→ Loading {filepath} → {TARGET_SCHEMA}.{table_name}")

    df = pd.read_csv(filepath)

    # Clean column headers (safe for Postgres)
    df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]

    df.to_sql(
        table_name,
        engine,
        schema=TARGET_SCHEMA,
        if_exists="append",
        index=False,
        method="multi",  # bulk insert
        chunksize=5000
    )

    print(f"✓ Loaded {len(df)} rows into {TARGET_SCHEMA}.{table_name}")


# -----------------------------------------------------------
#  MAIN PIPELINE
# -----------------------------------------------------------

def main():
    print("Starting Airbnb Pipeline…")

    engine = create_engine(DB_URL, echo=False, future=True)

    # 1. Wait for Postgres to finish running init SQL scripts
    wait_for_db(engine)

    # 2. Load each CSV to its target table
    for table_name, files in CSV_FILES.items():
        for filename in files:
            load_csv_to_db(engine, filename, table_name)

    print("✓ Pipeline completed successfully.")


# -----------------------------------------------------------
#  ENTRYPOINT
# -----------------------------------------------------------

if __name__ == "__main__":
    main()

import subprocess

print("▶ Running curated transformations...")
subprocess.run(["python", "transform_curated.py"], check=True)

print("▶ Running optimised transformations...")
subprocess.run(["python", "transform_optimised.py"], check=True)

print("🎉 Pipeline completed successfully")
from transform_curated import run_curated
from transform_optimised import run_optimised

run_curated()
run_optimised()

print("🎉 Pipeline completed")
