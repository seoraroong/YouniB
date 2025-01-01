from fastapi import FastAPI, HTTPException, Form, Request
from pydantic import BaseModel
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
import json
import torch
import logging
import re
from dotenv import load_dotenv
import os
from peft import PeftModel


app = FastAPI()

load_dotenv()

# 로그 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("model_inference")

# 모델 경로 설정
BASE_MODEL_PATH = "meta-llama/Llama-3.1-8B-Instruct"
QUIZ_MODEL_PATH = "/home/work/younib/fastapi-app/model/generate_quiz" 
SUMMARY_MODEL_PATH = "/home/work/younib/fastapi-app/model/generate_summary" 

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",  # NF4 양자화
    bnb_4bit_compute_dtype=torch.float16  # 계산 정확도를 유지하기 위해 float16 사용
)

# 요청 데이터 모델 정의
class InferenceRequest(BaseModel):
    json_path: str
    temperature: float = 1.0


def load_model(model_type: str):
    """
    필요한 모델을 동적으로 로드
    """
    if model_type == "quiz":
        tokenizer = AutoTokenizer.from_pretrained(QUIZ_MODEL_PATH)
        model = AutoModelForCausalLM.from_pretrained(
            QUIZ_MODEL_PATH,
            quantization_config=bnb_config,
            device_map="auto",
            trust_remote_code=True
        )
    elif model_type == "summary":
        tokenizer = AutoTokenizer.from_pretrained(SUMMARY_MODEL_PATH)
        base_model = AutoModelForCausalLM.from_pretrained(
            SUMMARY_MODEL_PATH,
            quantization_config=bnb_config,
            device_map="auto",
            trust_remote_code=True
        )
        model = PeftModel.from_pretrained(base_model, SUMMARY_MODEL_PATH)
        model.merge_and_unload()
        tokenizer.pad_token = "<|finetune_right_pad_id|>"
        model.resize_token_embeddings(len(tokenizer))
    else:
        raise ValueError("Invalid model type specified.")
    
    return tokenizer, model


def parse_generated_text(generated_text, question_type="MCQ"):
    """
    Parse question, options, and answer from generated text.
    Supports both MCQ and SAQ.
    """
    cleaned_text = re.sub(r"^.*?assistant.*?", "", generated_text, flags=re.IGNORECASE).strip()
    cleaned_text = re.sub(r"^question", "", cleaned_text, flags=re.IGNORECASE).strip()
    cleaned_text = re.sub(r"^:", "", cleaned_text).strip()

    if question_type == "MCQ":
        # Answer 찾기
        answer_patterns = [
            r'(?:ANSWER|_Answer_)\s*:?\s*([A-D](?:\)|\.)?.*?)(?:\n|$)',  # ANSWER: B 또는 _Answer_ B 형식
            r'(?:ANSWER|_Answer_)\s*:?\s*([A-D](?:\)|\.)?.*?)\s*$'       # 문서 끝에 있는 경우
        ]
        
        answer = "NotFound"
        for pattern in answer_patterns:
            answer_match = re.search(pattern, cleaned_text, re.IGNORECASE | re.MULTILINE)
            if answer_match:
                answer = answer_match.group(1).strip()
                text_until_answer = cleaned_text[:answer_match.start()]
                break
        else:
            text_until_answer = cleaned_text

        # Options 찾기
        options_header_pattern = r'(?:OPTIONS?:|CHOICES:)'
        options_header_match = re.search(options_header_pattern, text_until_answer, re.IGNORECASE)
        text_until_options = text_until_answer[:options_header_match.start()] if options_header_match else text_until_answer

        options_patterns = [
            r'(?:OPTIONS:|CHOICES:)?\s*(?:\n\s*)?([A-D](?:\)|\.|-)\s*.*?)(?=\n\s*[A-D](?:\)|\.|-)|$)',  # 일반적인 옵션 형식
            r'(?:\n\s*)([A-D](?:\)|\.)\s*.*?)(?=\n\s*[A-D](?:\)|\.)|$)'  # 레이블 없는 옵션
        ]

        options = []
        for pattern in options_patterns:
            options = re.findall(pattern, text_until_answer, re.MULTILINE)
            options = [opt.strip() for opt in options if opt.strip()]
            if len(options) >= 4:  # 유효한 옵션을 찾았다면
                break

        if not options:
            options = ["A) Not Found", "B) Not Found", "C) Not Found", "D) Not Found"]

        # Question 찾기 (Options 위치 이전의 텍스트에서 찾기)
        question_patterns = [
            r'(?:QUESTION|question|Question|uestion)s?:?\s*\n?\s*(.*?)(?=\s*(?:OPTIONS?:|CHOICES:|[A-D](?:\)|\.)))',  # QUESTION: 형식
            r'(?:QUESTION|question|Question|uestion)s?_\s*\n?\s*(.*?)(?=\s*(?:OPTIONS?:|CHOICES:|[A-D](?:\)|\.)))'    # question_ 형식
        ]
        question = "NotFound"
        for pattern in question_patterns:
            question_match = re.search(pattern, text_until_options, re.IGNORECASE | re.MULTILINE | re.DOTALL)
            if question_match:
                question = question_match.group(1).strip()
                break
        if question == "NotFound" and "A) Not Found" not in options:
            question = text_until_options.strip()

        # 결과 출력
        print('='*25)
        print('='*25)
        print('='*10,'파싱된 텍스트','='*10)
        print('='*25)

        print(f'Question:\n{question}')
        print(f'Options:\n{options}')
        print(f'Answer:\n{answer}\n')
        print('MCQ parsing 프로세스 종료\n\n')

        return {
            "question": question,
            "options": options,
            "answer": answer
        }

    elif question_type == "SAQ":
        # Answer 패턴들
        answer_patterns = [
            r"(?:ANSWER|Answer|_Answer_)\s*:?\s*(.*?)(?:\n|$)",  # 일반적인 형식
            r"(?:ANSWER|Answer|_Answer_)\s*:?\s*(.*?)\s*$"       # 문서 끝에 있는 경우
        ]
        
        # Answer 찾기
        answer = "NotFound"
        text_until_answer = cleaned_text
        for pattern in answer_patterns:
            answer_match = re.search(pattern, cleaned_text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
            if answer_match:
                answer = answer_match.group(1).strip()
                text_until_answer = cleaned_text[:answer_match.start()]
                break
        
        # Question 패턴들
        question_patterns = [
            r"(?:QUESTION|Question|uestion)\s*:?\s*\n?\s*(.*?)(?=\s*(?:ANSWER|Answer|_Answer_))",  # QUESTION: 형식
            r"(?:QUESTION|Question|uestion)_\s*\n?\s*(.*?)(?=\s*(?:ANSWER|Answer|_Answer_))",      # Question_ 형식
            r"(?:QUESTION|Question|uestion)\s*:?\s*\n?\s*(.*?)$"                                   # 마지막 패턴
        ]

        # Question 찾기
        question = "NotFound"
        for pattern in question_patterns:
            question_match = re.search(pattern, text_until_answer, re.IGNORECASE | re.MULTILINE | re.DOTALL)
            if question_match:
                question = question_match.group(1).strip()
                # 중복된 "question:" 제거
                question_clean = re.sub(r'^(?:question|QUESTION)\s*:?\s*', '', question, flags=re.IGNORECASE)
                if question_clean:
                    question = question_clean
                break
        if question == "NotFound" and answer != "NotFound":
            question = text_until_answer.strip()
        
        # 결과 출력
        print('='*25)
        print('='*25)
        print('='*10,'파싱된 텍스트','='*10)
        print('='*25)
        
        print(f'Question:\n{question}')
        print(f'Answer:\n{answer}\n')
        print('SAQ parsing 프로세스 종료\n\n')

        return {
            "question": question,
            "answer": answer
        }

    else:
        raise ValueError("Invalid question type specified.")



def parse_summary(summary_text):
    """Parse and clean summary text without character limit."""
    # Remove assistant tag if present
    summary_text = re.sub(r".*?assistant.*?\n", "", summary_text, flags=re.S).strip()

    # Extract summary content
    summary_match = re.search(r"Summary:\s*(.+)", summary_text, flags=re.S|re.IGNORECASE)
    if summary_match:
        cleaned_content = summary_match.group(1).strip()
    else:
        cleaned_content = summary_text.strip()

    # Clean unwanted sections
    cleaned_content = re.sub(
        r"(\*\*Section Title \d+\*\*\s*Content for section \d+\.\n*)", "", cleaned_content, flags=re.S
    )
    cleaned_content = re.sub(
        r"Provide concise and accurate summaries for each section\. Focus on key points only\.", "", cleaned_content
    )
    cleaned_content = re.sub(
        r"user\s*Context.*?assistant", "", cleaned_content, flags=re.S
    ).strip()

    # Clean whitespace
    cleaned_content = re.sub(r"\s+", " ", cleaned_content).strip()

    # Extract sections
    sections = re.findall(r"\*\*(.+?)\*\*\s*(.+?)(?=(\*\*|$))", cleaned_content, re.S)

    if sections:
        # Combine sections
        combined_summary = "\n\n".join(
            f"{section[0].strip()}:\n{section[1].strip()}" for section in sections
        )
        return {"summary_text": combined_summary}

    return {"summary_text": cleaned_content}


def preprocess_data(examples, tokenizer, task="quiz"):
    if task == 'summary':
        MAX_TOKENS = 1024
    else:
        MAX_TOKENS = 3200

    model_inputs = {
        "input_ids": [],
        "attention_mask": [],
        "labels": []
    }

    for input_text, output_text in zip(examples["input_text"], examples["output_text"]):

        # Context가 삽입된 위치를 파악
        if task=='summary':
            context_start_index = input_text.find("The context is:") + len("The context is:")
            if context_start_index == -1:
                logger.error(f"Invalid prompt format: 'Context:' not found in {input_text}")
                raise ValueError("Prompt format is invalid. 'Context:' not found.")
        else:
            context_start_index = input_text.find("Context: ") + len("Context: ")
            if context_start_index == -1:
                logger.error(f"Invalid prompt format: 'Context:' not found in {input_text}")
                raise ValueError("Prompt format is invalid. 'Context:' not found.")

        # 프롬프트 앞부분과 뒷부분 분리
        prompt_prefix = input_text[:context_start_index]  # "Context:" 포함
        if task == 'summary':
            context_end_index = input_text.find("Generate a concise")
        else:
            context_end_index = input_text.find("Now create", context_start_index)
        if context_end_index == -1:
            logger.error(f"Invalid prompt format: 'Now create' not found in {input_text}")
            raise ValueError("Prompt format is invalid. 'Now create' not found after context.")

        # Context 추출
        context = input_text[context_start_index:context_end_index].strip()
        prompt_prefix = input_text[:context_start_index]  # "Context:" 포함
        prompt_suffix = input_text[context_end_index:].strip()

        # 프롬프트 앞/뒤의 고정 길이를 계산
        prompt_prefix_ids = tokenizer(
            prompt_prefix,
            truncation=False,
            add_special_tokens=False
        )["input_ids"]
        prompt_suffix_ids = tokenizer(
            prompt_suffix,
            truncation=False,
            add_special_tokens=False
        )["input_ids"]

        fixed_prompt_length = len(prompt_prefix_ids) + len(prompt_suffix_ids)

        # Context에 할당된 최대 길이 계산
        max_context_length = MAX_TOKENS - fixed_prompt_length

        # Context 토큰화 및 잘라내기
        context_ids = tokenizer(
            context,
            truncation=True,
            max_length=max_context_length,
            padding=False,
            add_special_tokens=False
        )["input_ids"]

        # 최종 프롬프트 병합
        full_prompt_ids = prompt_prefix_ids + context_ids + prompt_suffix_ids
        attention_mask = [1] * len(full_prompt_ids)

        # 출력 텍스트 토큰화
        output_ids = tokenizer(
            output_text,
            truncation=True,
            max_length=192,
            padding="max_length",
            add_special_tokens=False
        )["input_ids"]

        # 입력과 출력 병합
        combined_ids = full_prompt_ids + output_ids
        combined_mask = attention_mask + [1] * len(output_ids)

        # 라벨 생성
        labels = [-100] * len(full_prompt_ids) + [
            token if token != tokenizer.pad_token_id else -100 for token in output_ids
        ]

        # 결과 저장
        model_inputs["input_ids"].append(combined_ids)
        model_inputs["attention_mask"].append(combined_mask)
        model_inputs["labels"].append(labels)
        
    logger.debug(f"Preprocessed input IDs: {model_inputs['input_ids'][:2]}")  # 첫 두 샘플만 확인
    logger.debug(f"Preprocessed attention masks: {model_inputs['attention_mask'][:2]}")  # 첫 두 샘플만 확인

    return model_inputs

def generate_text_with_preprocessing(prompt, model, tokenizer, temperature, task="quiz"):
    """
    Generate text with proper preprocessing using preprocess_data.
    """
    processed_data = preprocess_data({
        "input_text": [prompt],
        "output_text": [""]
    }, tokenizer, task=task)
    
    # Convert to tensors
    processed_inputs = {
        k: torch.tensor(v).to(model.device) for k, v in processed_data.items() if k != "labels"
    }
    if task == 'summary':
        # Generate text
        outputs = model.generate(
            **processed_inputs,
            max_new_tokens=150,
            num_beams=2,
            no_repeat_ngram_size=3,
            repetition_penalty=1.3,
            temperature=temperature,
            do_sample=True,
            top_p=0.9,
            early_stopping=True,
#            pad_token_id=tokenizer.pad_token_id
        )
    elif task == 'quiz':
        # Generate text
        outputs = model.generate(
            **processed_inputs,
            max_new_tokens=200,
            num_return_sequences=1,
            temperature=temperature,
            do_sample=True,
            top_p=0.90,
            pad_token_id=tokenizer.pad_token_id
        )
    input_ids_length = len(processed_inputs["input_ids"][0])
    decoded_output = tokenizer.decode(outputs[0][input_ids_length:], skip_special_tokens=True)
    return decoded_output

@app.post("/infer/")
async def infer(request: InferenceRequest):
    """
    JSON 경로를 받아 데이터를 처리하고,
    각 청크에 대해 두 모델을 사용해 인퍼런스를 수행합니다.
    """
    try:
        # JSON 데이터 로드
        with open(request.json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, list) or len(data) == 0:
            raise HTTPException(status_code=400, detail="Invalid JSON data")

        quiz_results = []
        summary_results = []
        
        # 퀴즈 생성 작업
        logger.info("Loading quiz model...")
        quiz_tokenizer, quiz_model = load_model("quiz")

        for chunk in data:
            start_page = chunk.get("start_page", -1)
            end_page = chunk.get("end_page", -1)
            context = chunk.get("text", "")

            if not context:
                logger.warning(f"Skipping empty context for pages {start_page}-{end_page}.")
                continue
            
            logger.info(f"Processed context for quiz generation: {context}")  # 너무 긴 경우 앞부분만 출력


            # **퀴즈 생성**
            # 객관식(MCQ) 프롬프트
            mcq_prompt = """<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are an expert in generating quizzes.
Given the context regarding biology, create a single multiple-choice question that accurately tests knowledge based on the context.

Context: {0}

If you decide to provide a quiz, you MUST strictly follow the format below:
The format for the multiple-choice quiz is:

  Question: <Your Question Here>
  Options:
  <Option A>
  <Option B>
  <Option C>
  <Option D>
  Answer: <Correct Option>

Additional rules:
1. Include exactly four options in the \"Options\" list.
2. Avoid repeating any information across the options.
3. Ensure that one and only one option is correct.
4. Ensure that the question and options are directly related to the provided context.
5. You SHOULD NOT include any other text in the response.
<|eot_id|><|start_header_id|>user<|end_header_id|>

Now create a single multiple-choice question.
<|eot_id|><|start_header_id|>assistant<|end_header_id|>
""".format(context)
            
            logger.info(f"Generated MCQ prompt: {mcq_prompt}")

            # 단답형(SAQ) 프롬프트
            saq_prompt = """<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are an expert in generating quizzes.
Given the context regarding biology, create a single short-answer question that accurately tests knowledge based on the context.

Context: {0}

If you decide to provide a quiz, you MUST strictly follow the format below:

Question: <Your Question Here>
Answer: <Correct Answer>

Additional rules:
1. Ensure the question and answer are directly related to the provided context.
2. Include only one correct answer.
3. You SHOULD NOT include any other text in the response.
<|eot_id|><|start_header_id|>user<|end_header_id|>

Now create a single short-answer question.
<|eot_id|><|start_header_id|>assistant<|end_header_id|>
""".format(context)

            # MCQ 생성
            mcq_text = generate_text_with_preprocessing(mcq_prompt, quiz_model, quiz_tokenizer, 0.75)
            mcq_parsed = parse_generated_text(mcq_text)

            # SAQ 생성
            saq_text = generate_text_with_preprocessing(saq_prompt, quiz_model, quiz_tokenizer, 0.75)
            saq_parsed = parse_generated_text(saq_text, question_type="SAQ")

            # 결과 저장
            quiz_results.append({
                "start_page": start_page,
                "end_page": end_page,
                "question_type": "MCQ",
                **mcq_parsed
            })
            quiz_results.append({
                "start_page": start_page,
                "end_page": end_page,
                "question_type": "SAQ",
                **saq_parsed
            })
            
        # 퀴즈 모델 메모리 해제
        del quiz_model
        torch.cuda.empty_cache()
        logger.info("Quiz model unloaded.")

        # 요약 생성 작업
        logger.info("Loading summary model...")
        summary_tokenizer, summary_model = load_model("summary")
            
        for chunk in data:
            start_page = chunk.get("start_page", -1)
            end_page = chunk.get("end_page", -1)
            context = chunk.get("text", "")

            if not context:
                logger.warning(f"Skipping empty context for pages {start_page}-{end_page}.")
                continue

            # 요약 생성
            summary_prompt = """<|begin_of_text|><|start_header_id|>system<|end_header_id|>

You are an expert summarizer. You are given a context regarding biology.
Based on the context, you need to generate a concise and clear summary to achieve the goal.

If you decide to provide a summary, you MUST strictly follow the format below:
The format for the summary is:

Summary: <Your Summary Here>

Additional rules you MUST follow:
1. The summary must be no longer than 3 sentences.
2. Ensure the summary captures the key points from the context.
3. Use simple and clear language, avoiding technical jargon unless necessary.

You SHOULD NOT include any other text in the response.
<|eot_id|><|start_header_id|>user<|end_header_id|>

The context is:
{0}
Generate a concise summary based on the context.
<|eot_id|><|start_header_id|>assistant<|end_header_id|>
""".format(context)
            summary_text = generate_text_with_preprocessing(summary_prompt, summary_model, summary_tokenizer, 0.7, task="summary")
            parsed_summary = parse_summary(summary_text)
            print('@@@@@@@@@@@@@@ 요약 결과 @@@@@@@@@@@@@@')
            print(parsed_summary)

            summary_results.append({
                "start_page": start_page,
                "end_page": end_page,
                "summary_text": parsed_summary["summary_text"]
            })
                
        # 요약 모델 메모리 해제
        del summary_model
        torch.cuda.empty_cache()
        logger.info("Summary model unloaded.")

        response_payload = {
            "quiz_results": quiz_results,
            "summary_results": summary_results,
        }

        logger.info("결과 데이터 (응답으로 전달):")
        logger.info(json.dumps(response_payload, indent=4, ensure_ascii=False))

        return response_payload

    except FileNotFoundError:
        logger.error("JSON file not found.")
        raise HTTPException(status_code=404, detail="JSON file not found.")
    except torch.cuda.OutOfMemoryError:
        logger.error("CUDA out of memory error.")
        torch.cuda.empty_cache()
        raise HTTPException(status_code=500, detail="CUDA out of memory error.")
    except Exception as e:
        logger.error("An error occurred during inference", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred")

@app.get("/test")
async def test_endpoint():
    """
    테스트용 엔드포인트.
    """
    return {"message": "Model inference server is running."}
