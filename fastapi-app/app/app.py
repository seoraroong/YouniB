from fastapi import FastAPI, UploadFile, HTTPException, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import os
import json
import subprocess
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import logging

logging.basicConfig(level=logging.DEBUG)  # 로그 수준을 debug로 설정
logger = logging.getLogger("uvicorn")

# FastAPI 앱 초기화
app = FastAPI()

# CORS 미들웨어 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 또는 `["http://127.0.0.1:8000"]`로 Django URL을 명시할 수 있습니다.
    allow_credentials=True,
    allow_methods=["*"],  # 모든 HTTP 메서드 허용
    allow_headers=["*"],  # 모든 헤더 허용
)

# # 디렉토리 설정
BASE_DIR = "/home/work/YOUNIB/fastapi-app"
# STATIC_DIR = os.path.join(BASE_DIR, "static")
# app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

UPLOAD_FOLDER = "./temp_folder"
OUTPUT_FOLDER = "./output_folder"
TRIGGER_FOLDER = "./trigger_folder"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(TRIGGER_FOLDER, exist_ok=True)

# 템플릿 설정 (HTML 템플릿을 사용하기 위해 설정)
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# MinerU 명령어 실행 함수
def run_mineru(pdf_path):
    try:
        mineru_command = [
            "magic-pdf",              # MinerU 명령어
            "-p", pdf_path,           # PDF 파일 경로
            "-o", "./output_folder",  # 출력 디렉토리
            "--method", "auto"        # 자동 처리 방식
        ]
        subprocess.run(mineru_command, check=True)  # subprocess로 명령어 실행
        print(f"MinerU processing completed for: {pdf_path}")
    except subprocess.CalledProcessError as e:
        print(f"Error during MinerU processing: {e}")
        raise RuntimeError("Failed to process PDF with MinerU.")

# 처리된 PDF에서 content_list.json 파일 찾는 함수
def find_content_json(output_dir):
    for root, dirs, files in os.walk(output_dir):
        for file in files:
            if file.endswith("_content_list.json"):
                print(f"Found content_list.json: {os.path.join(root, file)}")
                return os.path.join(root, file)
    raise FileNotFoundError("No _content_list.json file found in the output directory.")

# content_list.json 파일을 처리하는 함수
def preprocess_content_json(content_json_path, output_path):
    with open(content_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    processed_data = [
        item.get("text", "").strip()
        for item in data if item.get("type") == "text" and len(item.get("text", "").strip()) > 0
    ]

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(processed_data, f, ensure_ascii=False, indent=4)

    print(f"Processed content saved to: {output_path}")
    return output_path

# 업로드 페이지로 이동하는 뷰
@app.get("/", response_class=HTMLResponse)
async def upload_page(request: Request):
    return templates.TemplateResponse("pdf_processor/upload.html", {"request": request})

# PDF 처리 요청을 처리하는 뷰
@app.post("/process-pdf/")
async def process_pdf(file: UploadFile):
    print(f"Received file: {file.filename}")

    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")

     # 파일이 잘 전달되었는지 로그 출력
    logging.info(f"Received PDF file: {file.filename}, size: {file.size} bytes")

    # PDF 파일을 지정된 경로에 저장
    pdf_path = os.path.join(UPLOAD_FOLDER, file.filename)
    with open(pdf_path, "wb") as f:
        f.write(await file.read())

    print(f"File saved at: {pdf_path}")  # 파일 저장 위치 출력

    # 파일 저장 후 로그 출력
    logging.info(f"File saved to {pdf_path}")

    # MinerU 실행
    try:
        run_mineru(pdf_path)
    except RuntimeError as e:
        logging.error(f"Error during MinerU processing: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    # 처리된 PDF에서 _content_list.json 파일 찾기
    try:
        content_json_path = find_content_json(OUTPUT_FOLDER)
    except FileNotFoundError as e:
        logging.error(f"Error finding content JSON file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    # JSON 파일 처리
    processed_json_path = os.path.join(OUTPUT_FOLDER, f"{file.filename}.processed.json")
    preprocess_content_json(content_json_path, processed_json_path)

    # 트리거 파일 생성
    trigger_file = os.path.join(TRIGGER_FOLDER, f"{file.filename}.trigger")
    with open(trigger_file, "w") as f:
        f.write(processed_json_path)

    # 로그에 처리 결과 출력
    logging.info(f"Processed content JSON saved to: {processed_json_path}")

    # 결과 JSON 파일 경로 반환
    return {"message": "PDF processed successfully.", "json_path": processed_json_path}

@app.get("/test")
async def test_endpoint():
    logger.debug("Debug message from FastAPI")
    logger.info("Info message from FastAPI")
    return {"message": "Test endpoint is working!"}
