"""Full profile only: the nightly pipeline as an Airflow DAG (SDD 6.1).

In the lite profile APScheduler inside the API runs the same jobs. Both call the API's job
endpoints with the pipeline service account, so roles and audit apply the same way.
"""

from __future__ import annotations

import os
from datetime import datetime

import requests
from airflow import DAG
from airflow.operators.python import PythonOperator

API = os.environ.get("VOLTGUARD_API", "http://api:8000")


def _call(path: str) -> None:
    token = requests.post(f"{API}/auth/token", json={
        "username": "pipeline", "password": os.environ["PIPELINE_PASSWORD"]}, timeout=30).json()["access_token"]
    response = requests.post(f"{API}{path}", headers={"Authorization": f"Bearer {token}"}, timeout=3600)
    response.raise_for_status()


with DAG("voltguard_nightly", start_date=datetime(2026, 1, 1), schedule="0 3 * * *", catchup=False) as dag:
    detect = PythonOperator(task_id="run_detection", python_callable=_call, op_args=["/jobs/run-detection"])
    cases = PythonOperator(task_id="create_cases", python_callable=_call, op_args=["/jobs/create-cases"])
    detect >> cases
