# Интеграция Airflow

Добавляются DAG и скрипт исполнения ноутбука. Скрипт заменяет путь Kaggle только
в копии в памяти, выполняет все ячейки и добавляет экспорт итоговой таблицы.

## Подключение в Ubuntu / WSL2

Распакуйте содержимое архива в ~/projects/ML-Project (или в другую директорию с вашими проектами, это просто пример). Если .gitignore уже
существует, объедините правила, сохранив предыдущие.

В окружении проекта выполните:

```bash
cd ~/projects/ML-Project
source .venv/bin/activate
uv pip install nbclient ipykernel
python -m ipykernel install --sys-prefix --name flight-delay --display-name "Flight Delay (Python 3.12)"
python scripts/run_notebook.py check-data
```

CSV должен находиться в data/flights.csv (в проекте должна быть директория для хранения датасетов, как пример data). Kernel flight-delay регистрируется
внутри окружения проекта, чтобы ноутбук использовал именно его библиотеки.

В другом терминале запустите Airflow:

```bash
source ~/venvs/airflow/bin/activate
export AIRFLOW_HOME="$HOME/airflow"
export AIRFLOW__CORE__LOAD_EXAMPLES=False
export FLIGHT_PROJECT_DIR="$HOME/projects/ML-Project"
export AIRFLOW__CORE__DAGS_FOLDER="$FLIGHT_PROJECT_DIR/dags"
python -c "from airflow.providers.standard.operators.bash import BashOperator; print('BashOperator OK')"
airflow dags list-import-errors
airflow standalone
```

Экспортированные переменные нужно задавать при каждом запуске в новом
терминале. При другом расположении репозитория измените FLIGHT_PROJECT_DIR.
Данный DAG рассчитан на Airflow 3.x. Если импорт BashOperator не работает:

```bash
uv pip install "apache-airflow==3.3.2" apache-airflow-providers-standard --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-3.3.2/constraints-3.12.txt"
```

Откройте http://localhost:8080, найдите flight_delay_notebook, включите DAG
переключателем, если он на паузе, и нажмите Trigger.

Задачи: check_data → run_notebook → check_results.

## Результаты

Папка outputs/<хеш ID запуска>/ содержит:
- run_id.txt – исходный ID запуска Airflow;
- executed.ipynb – выполненную копию ноутбука, включая ошибку при сбое;
- metrics.csv – итоговую таблицу из раздела Final test при успешном выполнении.

Путь к папке и номера выполняемых ячеек видны в логах run_notebook.

## Завершение

Ctrl+C в терминале standalone.
