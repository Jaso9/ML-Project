"""Execute the original notebook without changing the file on disk."""
import argparse
import hashlib
import os
from pathlib import Path

import nbformat
import pandas as pd
from nbclient import NotebookClient

PROJECT = Path(__file__).resolve().parents[1]
NOTEBOOK = PROJECT / "FlightDelayPrediction.ipynb"
CSV = PROJECT / "data" / "flights.csv"
KAGGLE_PATH = "/kaggle/input/datasets/usdot/flight-delays/flights.csv"
REQUIRED_COLUMNS = {
    "YEAR", "MONTH", "DAY", "DAY_OF_WEEK", "AIRLINE", "FLIGHT_NUMBER",
    "TAIL_NUMBER", "ORIGIN_AIRPORT", "DESTINATION_AIRPORT",
    "SCHEDULED_DEPARTURE", "DEPARTURE_TIME", "DEPARTURE_DELAY", "TAXI_OUT",
    "WHEELS_OFF", "SCHEDULED_TIME", "ELAPSED_TIME", "AIR_TIME", "DISTANCE",
    "WHEELS_ON", "TAXI_IN", "SCHEDULED_ARRIVAL", "ARRIVAL_TIME",
    "ARRIVAL_DELAY", "DIVERTED", "CANCELLED", "CANCELLATION_REASON",
    "AIR_SYSTEM_DELAY", "SECURITY_DELAY", "AIRLINE_DELAY",
    "LATE_AIRCRAFT_DELAY", "WEATHER_DELAY",
}


def result_dir():
    # Hashing avoids unsafe path characters in Airflow run IDs.
    run_id = os.environ.get("FLIGHT_RUN_ID", "local")
    key = hashlib.sha256(run_id.encode()).hexdigest()[:16]
    return PROJECT / "outputs" / key


def check_data():
    if not CSV.is_file():
        raise FileNotFoundError(f"Place the dataset here: {CSV}")
    sample = pd.read_csv(CSV, nrows=5)
    missing = REQUIRED_COLUMNS - set(sample.columns)
    if missing:
        raise ValueError(f"Missing CSV columns: {sorted(missing)}")
    if sample.empty:
        raise ValueError("The CSV contains no rows")
    if not NOTEBOOK.is_file():
        raise FileNotFoundError(NOTEBOOK)
    print(f"Input data found: {CSV}", flush=True)


def run():
    check_data()
    destination = result_dir()
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "run_id.txt").write_text(
        os.environ.get("FLIGHT_RUN_ID", "local"), encoding="utf-8"
    )
    # Remove old metrics before a retry so old results cannot imply success.
    (destination / "metrics.csv").unlink(missing_ok=True)
    notebook = nbformat.read(NOTEBOOK, as_version=4)
    replacements = 0
    for cell in notebook.cells:
        if cell.cell_type == "code":
            replacements += cell.source.count(KAGGLE_PATH)
            cell.source = cell.source.replace(KAGGLE_PATH, CSV.as_posix())
            cell.outputs = []
            cell.execution_count = None
    if replacements != 1:
        raise ValueError("Expected exactly one Kaggle CSV path in the notebook")
    notebook.cells.append(nbformat.v4.new_code_cell(
        "# Export the final table from the Final test section.\n"
        f"output.to_csv({str(destination / 'metrics.csv')!r}, index=False)\n"
        "print('Final metrics exported')"
    ))
    def progress(cell, cell_index):
        if cell.cell_type == "code":
            print(f"Executing cell {cell_index + 1}/{len(notebook.cells)}", flush=True)
    client = NotebookClient(
        notebook, kernel_name="flight-delay", timeout=None,
        allow_errors=False, resources={"metadata": {"path": str(destination)}},
        on_cell_start=progress,
    )
    print(f"Results directory: {destination}", flush=True)
    try:
        client.execute()
    finally:
        # Keep the executed portion and traceback even if a cell fails.
        nbformat.write(notebook, destination / "executed.ipynb")
    print("Notebook finished", flush=True)


def check_results():
    destination = result_dir()
    executed = nbformat.read(destination / "executed.ipynb", as_version=4)
    if any(
        output.get("output_type") == "error"
        for cell in executed.cells if cell.cell_type == "code"
        for output in cell.get("outputs", [])
    ):
        raise ValueError("The executed notebook contains an error")
    metrics = pd.read_csv(destination / "metrics.csv")
    columns = ["Model", "PR-AUC", "ROC-AUC"]
    if metrics.empty or not set(columns).issubset(metrics.columns):
        raise ValueError("The final metrics table is empty or invalid")
    scores = metrics[["PR-AUC", "ROC-AUC"]]
    if scores.isna().any().any() or not scores.ge(0).all().all() or not scores.le(1).all().all():
        raise ValueError("PR-AUC/ROC-AUC must be finite numbers between 0 and 1")
    print(metrics[columns].to_string(index=False), flush=True)
    print(f"Results checked: {destination}", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["check-data", "run", "check-results"])
    args = parser.parse_args()
    {"check-data": check_data, "run": run, "check-results": check_results}[args.command]()
