Basketball ETL Pipeline

This project demonstrates a full, production-ready ETL pipeline for ingesting basketball data from the API-Football Basketball API
, transforming it, and preparing it for analytics.

It includes:

Python ETL (requests, psycopg2, dotenv)

PostgreSQL raw & staging layers (JSONB & flattened tables)

Dockerized environment (Postgres + pgAdmin + Airflow)

dbt for transformations

Tableau-ready outputs

Git workflow with branches and Pull Requests

Table of Contents

Setup

Environment Variables

Docker Services

Python ETL

dbt Transformations

Airflow Orchestration

Tableau Visualization

Git Workflow

Next Steps

Setup

Clone the repo:

git clone https://github.com/ihilesen/portfolio.git
cd basketball-etl


Ensure you have installed:

Docker & Docker Compose

VS Code (optional)

Python 3.10+

Environment Variables

Create a .env file in project root:

# API
API_FOOTBALL_KEY=your_api_key_here

# Postgres
POSTGRES_DB=basketball
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=postgres

# Airflow
AIRFLOW_HOME=/opt/airflow

Docker Services

docker-compose.yml:

version: "3.8"

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: basketball
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  pgadmin:
    image: dpage/pgadmin4
    container_name: pgadmin
    environment:
      PGADMIN_DEFAULT_EMAIL: admin@admin.com
      PGADMIN_DEFAULT_PASSWORD: admin
    ports:
      - "5050:80"
    depends_on:
      - postgres

  extractor:
    build: .
    depends_on:
      - postgres

  airflow:
    image: apache/airflow:2.7.0
    environment:
      AIRFLOW__CORE__EXECUTOR: LocalExecutor
      AIRFLOW__CORE__FERNET_KEY: 'YOUR_RANDOM_KEY'
      AIRFLOW__CORE__LOAD_EXAMPLES: 'False'
    volumes:
      - ./dags:/opt/airflow/dags
    ports:
      - "8080:8080"
    depends_on:
      - postgres

volumes:
  postgres_data:

Python ETL

extract_games.py (raw ingestion):

import os, json, requests, psycopg2
from datetime import date, datetime
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_FOOTBALL_KEY")
RUN_DATE = date.today()
API_URL = "https://v1.basketball.api-sports.io/games"

HEADERS = {"x-apisports-key": API_KEY}

DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "postgres"),
    "dbname": os.getenv("POSTGRES_DB", "basketball"),
    "user": os.getenv("POSTGRES_USER", "postgres"),
    "password": os.getenv("POSTGRES_PASSWORD", "postgres"),
}

def fetch_games():
    response = requests.get(API_URL, headers=HEADERS, params={"date": RUN_DATE.isoformat()})
    print("STATUS:", response.status_code)
    response.raise_for_status()
    return response.json()["response"]

def load_to_postgres(data):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS raw_games (
            id SERIAL PRIMARY KEY,
            payload JSONB,
            run_date DATE,
            ingested_at TIMESTAMP
        );
    """)
    cur.execute("SELECT 1 FROM raw_games WHERE run_date=%s LIMIT 1;", (RUN_DATE,))
    if cur.fetchone():
        print("⚠️ Data already loaded today. Skipping.")
        cur.close(); conn.close(); return
    cur.execute(
        "INSERT INTO raw_games (payload, run_date, ingested_at) VALUES (%s, %s, %s);",
        (json.dumps(data), RUN_DATE, datetime.utcnow())
    )
    conn.commit(); cur.close(); conn.close()
    print("✅ Raw games data loaded successfully")

if __name__ == "__main__":
    games = fetch_games()
    load_to_postgres(games)

dbt Transformations

Install dbt:

pip install dbt-core dbt-postgres


Initialize dbt project:

dbt init basketball_dbt


Example staging model stg_games.sql:

WITH raw AS (
    SELECT
        game->>'id' AS game_id,
        game->'league'->>'name' AS league_name,
        game->'teams'->'home'->>'name' AS home_team,
        game->'teams'->'away'->>'name' AS away_team,
        run_date
    FROM {{ ref('raw_games') }},
    LATERAL jsonb_array_elements(payload) AS game
)
SELECT * FROM raw;


Run dbt models:

dbt run

Airflow Orchestration

Create a DAG dags/basketball_etl_dag.py:

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
from extract_games import fetch_games, load_to_postgres

def etl_task():
    data = fetch_games()
    load_to_postgres(data)

with DAG(
    'basketball_etl',
    start_date=datetime(2026,1,21),
    schedule_interval='@daily',
    catchup=False
) as dag:
    run_etl = PythonOperator(task_id='run_etl', python_callable=etl_task)


Access Airflow UI:

http://localhost:8080


Trigger DAG → Daily ETL runs

Tableau Visualization

Connect Tableau → Postgres (basketball DB)

Use stg_games as source

Build dashboards:

Number of games per day

League distribution

Home vs Away team stats

Git Workflow

Create branch:

git checkout -b basketball-etl


Stage & commit:

git add .
git commit -m "Add full ETL pipeline with dbt & Airflow"


Push:

git push -u origin basketball-etl


Open a Pull Request → Merge into main
