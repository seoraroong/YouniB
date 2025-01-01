# Airflow 공식 이미지 사용
FROM apache/airflow:2.7.2-python3.9

# 환경 변수 설정
ENV AIRFLOW_HOME=/opt/airflow

# 작업 디렉토리 설정
WORKDIR $AIRFLOW_HOME

# 필요한 시스템 패키지 설치
USER root
RUN apt-get update && apt-get install -y \
    build-essential \
    libssl-dev \
    libffi-dev \
    libpq-dev \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 사용자 권한 복구
USER airflow

# Python 패키지 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# DAGs, plugins 및 기타 파일 복사
COPY dags/ $AIRFLOW_HOME/dags/
COPY plugins/ $AIRFLOW_HOME/plugins/

# 서비스 계정 키 복사 (옵션)
COPY google-drive-apikey.json $AIRFLOW_HOME/

# Entrypoint 실행
ENTRYPOINT ["tini", "--", "entrypoint"]
CMD ["webserver"]
