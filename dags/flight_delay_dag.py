"""Manual execution of the existing research notebook (Airflow 3)."""
import os
from datetime import datetime, timezone
from pathlib import Path

from airflow.sdk import DAG
from airflow.providers.standard.operators.bash import BashOperator

PROJECT = Path(os.environ.get("FLIGHT_PROJECT_DIR", "~/projects/ML-Project")).expanduser()

with DAG(
    dag_id="flight_delay_notebook",
    description="Check flights.csv, execute the notebook, check exported metrics",
    start_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
    schedule=None,
    catchup=False,
    max_active_runs=1,
    default_args={"retries": 0},
    tags=["ml", "notebook"],
) as dag:
    tasks = []
    for task_id, command in [
        ("check_data", "check-data"),
        ("run_notebook", "run"),
        ("check_results", "check-results"),
    ]:
        tasks.append(BashOperator(
            task_id=task_id,
            bash_command=(
                'exec "$PROJECT_DIR/.venv/bin/python" -u '
                '"$PROJECT_DIR/scripts/run_notebook.py" ' + command
            ),
            env={"PROJECT_DIR": str(PROJECT), "FLIGHT_RUN_ID": "{{ run_id }}"},
            append_env=True,
            do_xcom_push=False,
        ))
    tasks[0] >> tasks[1] >> tasks[2]
