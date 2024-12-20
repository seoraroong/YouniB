from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
from airflow.providers.postgres.hooks.postgres import PostgresHook
from sqlalchemy import text
import json
import logging

def ensure_table_exists():
    create_table_query = """
    CREATE TABLE IF NOT EXISTS model_comparison_queue (
        id SERIAL PRIMARY KEY,
        input_data JSON NOT NULL,
        current_model_output JSON NOT NULL,
        new_model_output JSON NOT NULL,
        status VARCHAR(50) DEFAULT 'pending_for_review',
        user_feedback TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    engine = PostgresHook(postgres_conn_id='postgres_default').get_sqlalchemy_engine()
    with engine.connect() as conn:
        conn.execute(create_table_query)

def fetch_eval_data():
    # 하드코딩된 평가 데이터 대신 외부에서 로드
    return [{"id": 1, "text": "Example input text"}]

def generate_comparison_data():
    try:
        ensure_table_exists()
        eval_data = fetch_eval_data()
        engine = PostgresHook(postgres_conn_id='postgres_default').get_sqlalchemy_engine()
        with engine.connect() as conn:
            with conn.begin():
                for data in eval_data:
                    current_output = {"result": "Current model output"}
                    new_output = {"result": "New model output"}
                    conn.execute(
                        text("""
                            INSERT INTO model_comparison_queue (input_data, current_model_output, new_model_output)
                            VALUES (:input_data, :current_model_output, :new_model_output)
                        """),
                        {
                            'input_data': json.dumps(data),
                            'current_model_output': json.dumps(current_output),
                            'new_model_output': json.dumps(new_output)
                        }
                    )
    except Exception as e:
        logging.error(f"Error generating comparison data: {e}")
        raise

with DAG(
    dag_id='model_comparison_data_dag',
    start_date=datetime(2023, 1, 1),
    schedule_interval=None,
    catchup=False,
) as dag:
    generate_comparison_data_task = PythonOperator(
        task_id='generate_comparison_data',
        python_callable=generate_comparison_data,
    )
