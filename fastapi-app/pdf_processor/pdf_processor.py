from contextlib import AsyncExitStack
from fastapi import FastAPI, UploadFile, HTTPException, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
import os
import json
import subprocess
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import logging
import httpx 
import warnings
import asyncio
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Dict

warnings.filterwarnings("ignore", message="The attention mask and the pad token id were not set")

# Django 서버 URL
DJANGO_API_URL = "http://127.0.0.1:8000/api/create-quiz/" 

DJANGO_SERVER_URL = "http://127.0.0.1:8000"

# model_inference 서버 URL
MODEL_INFERENCE_URL = "http://127.0.0.1:8081/infer/"

logging.basicConfig(level=logging.DEBUG)  # 로그 수준을 debug로 설정
logger = logging.getLogger("uvicorn")

# FastAPI 앱 초기화
app = FastAPI()

class TimeoutMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, timeout: int):
        super().__init__(app)
        self.timeout = timeout

    async def dispatch(self, request: Request, call_next):
        try:
            return await asyncio.wait_for(call_next(request), timeout=self.timeout)
        except asyncio.TimeoutError:
            return JSONResponse(
                {"detail": "Request timed out"}, status_code=504
            )
            
app.add_middleware(TimeoutMiddleware, timeout=300)

# CORS 미들웨어 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 또는 `["http://127.0.0.1:8000"]`로 Django URL을 명시할 수 있습니다.
    allow_credentials=True,
    allow_methods=["*"],  # 모든 HTTP 메서드 허용
    allow_headers=["*"],  # 모든 헤더 허용
)

# 디렉토리 설정
BASE_DIR = "/home/work/YOUNIB/fastapi-app"
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
def preprocess_content_json(content_json_path, output_path, window_size=5, stride=3):
    """
    _content_list.json 파일을 슬라이딩 윈도우 방식으로 처리하고,
    페이지 텍스트와 인덱스를 매핑한 JSON을 생성합니다.

    Args:
        content_json_path (str): _content_list.json 파일 경로
        output_path (str): 결과 JSON 파일 경로
        window_size (int): 슬라이딩 윈도우 크기
        stride (int): 슬라이딩 윈도우의 이동 간격
    Returns:
        str: 결과 JSON 파일 경로
    """
    with open(content_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    # 페이지별 텍스트를 매핑
    page_text_mapping = {}
    for item in data:
        if item.get("type") == "text" and len(item.get("text", "").strip()) > 0:
            page_idx = item.get("page_idx", -1)
            if page_idx not in page_text_mapping:
                page_text_mapping[page_idx] = []
            page_text_mapping[page_idx].append(item.get("text").strip())

    # 페이지별 텍스트 병합
    sorted_pages = sorted(page_text_mapping.keys())
    merged_text = {
        page_idx: " ".join(page_text_mapping[page_idx]) for page_idx in sorted_pages
    }

    # 슬라이딩 윈도우 적용
    chunks = []
    max_page = max(sorted_pages)
    for start_page in range(0, max_page + 1, stride):
        end_page = start_page + window_size - 1
        window_text = []
        included_pages = []
        for page_idx in range(start_page, end_page + 1):
            if page_idx in merged_text:
                window_text.append(merged_text[page_idx])
                included_pages.append(page_idx)
        if window_text:  # 내용이 있을 경우만 추가
            chunks.append({
                "start_page": start_page,
                "end_page": end_page,
                "included_pages": included_pages,  # 포함된 페이지 정보 추가
                "text": " ".join(window_text)
            })

    # 결과 저장
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=4)

    print(f"Processed content saved to: {output_path}")
    return output_path


async def send_to_django(quiz_data, client):
    response = await client.post(DJANGO_API_URL, json=quiz_data)
    response.raise_for_status()
    return response.json()


# PDF 처리 요청을 처리하는 뷰
@app.post("/process-pdf/")
async def process_pdf(file: UploadFile, course_material_id: int = Form(...)):
    logging.info(f"Received file: {file.filename} with course_material_id: {course_material_id}")

    """
    업로드된 PDF 파일 처리, 모델 추론 수행, Django 서버로 퀴즈 데이터 전송
    """
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")

    # PDF 저장
    pdf_path = os.path.join(UPLOAD_FOLDER, file.filename)
    with open(pdf_path, "wb") as f:
        f.write(await file.read())
    logging.info(f"PDF 파일 저장 완료: {pdf_path}")

    # MinerU 실행
    try:
        run_mineru(pdf_path)

        # PDF 파일명 기반 content_list.json 경로 생성
        pdf_base_name = os.path.splitext(file.filename)[0]  # 확장자 제거
        content_json_path = os.path.join(
            OUTPUT_FOLDER, pdf_base_name, "auto", f"{pdf_base_name}_content_list.json"
        )
        if not os.path.exists(content_json_path):
            raise FileNotFoundError(f"Content list file not found: {content_json_path}")

        # content_list.json 파일을 전처리
        processed_json_path = os.path.join(OUTPUT_FOLDER, f"{file.filename}.processed.json")
        preprocess_content_json(content_json_path, processed_json_path)
        logging.info(f"Content list JSON 파일 전처리 완료: {processed_json_path}")

    except Exception as e:
        logging.error(f"PDF 처리 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"PDF 처리 실패: {str(e)}")
    
    # 모델 추론 요청
    try:
        async with httpx.AsyncClient(timeout=300) as client:
            response = await client.post(
                MODEL_INFERENCE_URL, json={"json_path": processed_json_path}
            )
            logging.info(f"HTTP 응답 상태 코드: {response.status_code}")
            response.raise_for_status()
            inference_result = response.json()
            logging.info(f"모델 추론 결과:\n{json.dumps(inference_result, indent=2, ensure_ascii=False)}")

            # 퀴즈 결과 정리
            quiz_results = [
                {
                    "question": r.get("question"),
                    "question_type": r.get("question_type"),
                    "options": r.get("options"),
                    "answer": r.get("answer"),
                    "start_page": r.get("start_page"),
                    "end_page": r.get("end_page"),
                    "course_material_id": course_material_id,
                }
                for r in inference_result.get("quiz_results", [])
            ]

            # 요약 결과 정리
            summary_results = [
                {
                    "summary_text": r.get("summary_text"),
                    "course_material_id": course_material_id,
                }
                for r in inference_result.get("summary_results", [])
            ]
            logging.info(f"퀴즈 및 요약 결과 정리 완료")
    except httpx.HTTPStatusError as e:
        logging.error(f"HTTP 요청 실패: {e.response.status_code} - {e.response.text}")
        raise HTTPException(status_code=500, detail=f"HTTP 요청 실패: {e.response.status_code}")
    except json.JSONDecodeError as e:
        logging.error(f"JSON 디코딩 실패: {e} - 응답 텍스트: {response.text}")
        raise HTTPException(status_code=500, detail="Invalid JSON response from model inference server")
    except Exception as e:
        logging.error(f"모델 추론 실패: {str(e)}")
        raise HTTPException(status_code=500, detail="모델 추론 실패")
    
    # Django 서버로 퀴즈 데이터 전송
    django_quiz_url = "http://127.0.0.1:8000/studyarchive/api/save-quiz/"  # Django API 엔드포인트
    django_summary_url = f"http://127.0.0.1:8000/studyarchive/api/save-summary/"
    
    try:
        async with httpx.AsyncClient() as client:
            # 요약 데이터 전송
            summary_payload = {"course_material_id": course_material_id, "results": summary_results}
            summary_response = await client.post(django_summary_url, json=summary_payload)
            summary_response.raise_for_status()
            logging.info(f"Django 서버로 요약 데이터 전송 성공: {summary_response.json()}")

            # 퀴즈 데이터 전송
            quiz_payload = {"course_material_id": course_material_id, "results": quiz_results}
            quiz_response = await client.post(django_quiz_url, json=quiz_payload)
            quiz_response.raise_for_status()
            logging.info(f"Django 서버로 퀴즈 데이터 전송 성공: {quiz_response.json()}")

    except Exception as e:
        logging.error(f"Django 서버 전송 실패: {str(e)}")
        raise HTTPException(status_code=500, detail="Django 서버 전송 실패")
    
    # 인퍼런스 결과 반환
    return {
        "message": "PDF 처리 및 모델 추론 성공",
        "quiz_results": quiz_results,
        "summary_results": summary_results,
    }


