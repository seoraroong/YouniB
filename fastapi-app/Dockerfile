# 1. Base Python 3.10 이미지
FROM python:3.10-slim

# 2. 작업 디렉토리 설정
WORKDIR /app

# 3. 필수 시스템 패키지 설치
RUN apt-get update && apt-get install -y \
    python3-distutils \
    build-essential \
    && apt-get clean

# 4. 의존성 파일 복사 및 설치
COPY ./requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. 소스 코드 복사
COPY . .

# 6. 실행 포트 설정
EXPOSE 5000

# 7. 기본 명령어 (Uvicorn으로 FastAPI 실행)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000", "--reload"]
