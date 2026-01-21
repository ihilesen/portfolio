import requests
import json
import psycopg2
from dotenv import load_dotenv
import os
from datetime import date
from datetime import datetime

load_dotenv()  # loads .env into environment

API_KEY = os.getenv("API_FOOTBALL_KEY")  # ✅ correct
RUN_DATE = date.today()

if not API_KEY:
    raise ValueError("API_FOOTBALL_KEY is not set")

HEADERS = {
    "x-apisports-key": API_KEY
}

# API endpoint
URL = "https://v1.basketball.api-sports.io/games"

# -----------------------------
# Step 1: Fetch function
# -----------------------------

def fetch_games():
    params = {"date": RUN_DATE.isoformat()}
    response = requests.get(
        "https://v1.basketball.api-sports.io/games",
        headers=HEADERS,
        params=params
    )
    print("STATUS:", response.status_code)
    response.raise_for_status()
    return response.json()


# -----------------------------
# Step 2: Load function
# -----------------------------
def load_to_postgres(data):
    """
    Inserts raw API JSON into raw_games table (idempotent by run_date).
    """
    conn = psycopg2.connect(
        host="postgres",
        dbname="basketball",
        user="postgres",
        password="postgres"
    )
    cur = conn.cursor()

    # Create table if not exists
    cur.execute("""
        CREATE TABLE IF NOT EXISTS raw_games (
            id SERIAL PRIMARY KEY,
            payload JSONB,
            run_date DATE,
            ingested_at TIMESTAMP
        );
    """)

    # Idempotency check (one load per day)
    cur.execute(
        "SELECT 1 FROM raw_games WHERE run_date = %s LIMIT 1;",
        (RUN_DATE,)
    )

    if cur.fetchone():
        print("⚠️ Data already loaded for today. Skipping.")
        cur.close()
        conn.close()
        return

    # Insert JSON (SERIALISED)
    cur.execute(
        """
        INSERT INTO raw_games (payload, run_date, ingested_at)
        VALUES (%s, %s, %s);
        """,
        (
            json.dumps(data),      # 👈 critical fix
            RUN_DATE,
            datetime.utcnow()
        )
    )

    conn.commit()
    cur.close()
    conn.close()

    print("✅ Raw games data loaded successfully")



# -----------------------------
# Step 3: Main
# -----------------------------
if __name__ == "__main__":
    games = fetch_games()        # <-- THIS is where fetch_games is called
    load_to_postgres(games)
