from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime

with DAG(
    dag_id="basketball_etl",
    start_date=datetime(2024, 1, 1),
    schedule_interval="@daily",
    catchup=False
):

    extract = BashOperator(
        task_id="extract_data",
        bash_command="docker compose run extractor"
    )

    transform = BashOperator(
        task_id="run_dbt",
        bash_command="dbt run --project-dir /dbt"
    )

    extract >> transform
