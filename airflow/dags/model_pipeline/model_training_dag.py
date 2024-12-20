from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.sensors.sql import SqlSensor
from datetime import datetime
from airflow.providers.postgres.hooks.postgres import PostgresHook
import subprocess
import pandas as pd
import os

# DAG 기본 설정
with DAG(
    dag_id='model_training_dag',
    start_date=datetime(2023, 1, 1),
    schedule_interval=None,  # 수동 실행 또는 특정 조건에서만 실행
    catchup=False,
) as dag:

    # 데이터 수 10,000개 이상 확인
    check_data_count = SqlSensor(
        task_id='check_data_count',
        conn_id='postgres_default',
        sql=""" 
            SELECT COUNT(*) >= 10000 
            FROM processed_data_queue 
            WHERE status = 'approved';
        """,
        mode='poke',  # 상태가 만족될 때까지 확인
        poke_interval=60,  # 60초마다 확인
        timeout=600,  # 최대 10분 대기
    )

    # 학습 데이터 준비 및 저장
    def prepare_training_data():
        engine = PostgresHook(postgres_conn_id='postgres_default').get_sqlalchemy_engine()
        query = """
            SELECT queue_id, reviewed_data
            FROM processed_data_queue
            WHERE status = 'approved';
        """
        training_batch_id = int(datetime.now().timestamp())  # 학습 배치 ID 생성
        insert_query = """
            INSERT INTO training_data (training_batch_id, reviewed_data)
            VALUES (%s, %s)
        """
        update_query = """
            UPDATE processed_data_queue
            SET status = 'archived'
            WHERE queue_id = %s
        """

        with engine.connect() as conn:
            df = pd.read_sql(query, conn)

            # 학습 데이터를 Postgres에 저장
            for _, row in df.iterrows():
                conn.execute(insert_query, (training_batch_id, row['reviewed_data']))
                conn.execute(update_query, (row['queue_id'],))

            # JSON 파일로 저장 (선택)
            os.makedirs('/opt/airflow/data', exist_ok=True)
            df['reviewed_data'].to_json('/opt/airflow/data/training_data.json', orient='records')

    prepare_training_data_task = PythonOperator(
        task_id='prepare_training_data',
        python_callable=prepare_training_data,
    )

    # 모델 학습 태스크
    def train_model_function():
        # 학습 스크립트를 실행
        subprocess.run([
            "python", "/opt/airflow/scripts/train_model.py",
            "--data", "/opt/airflow/data/training_data.json"
        ])

    train_model_task = PythonOperator(
        task_id='train_model',
        python_callable=train_model_function,
    )

    # 학습 데이터 아카이빙 태스크
    def archive_training_data():
        engine = PostgresHook(postgres_conn_id='postgres_default').get_sqlalchemy_engine()
        query = """
            INSERT INTO training_data_archive (training_batch_id, reviewed_data)
            SELECT training_batch_id, reviewed_data
            FROM training_data
        """
        cleanup_query = "DELETE FROM training_data"

        with engine.connect() as conn:
            conn.execute(query)
            conn.execute(cleanup_query)

    archive_training_data_task = PythonOperator(
        task_id='archive_training_data',
        python_callable=archive_training_data,
    )

    # 태스크 순서 정의
    check_data_count >> prepare_training_data_task >> train_model_task >> archive_training_data_task
