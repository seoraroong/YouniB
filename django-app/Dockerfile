# Python 3.10-slim 이미지를 기반으로 사용
FROM python:3.10-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 업데이트 및 필수 패키지 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \  
    python3-distutils \
    python3-apt \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# 의존성 파일 복사 및 패키지 설치
COPY requirements.txt .  
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt

# 소스 코드 복사
COPY . .  

# Django 실행에 필요한 환경 변수 설정
ENV PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=myproject.settings

# Django 개발 서버 실행
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
