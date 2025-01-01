from transformers import AutoTokenizer

QUIZ_MODEL_PATH = "/home/work/younib/fastapi-app/model/generate_quiz"
SUMMARY_MODEL_PATH = "/home/work/younib/fastapi-app/model/generate_summary"

quiz_tokenizer = AutoTokenizer.from_pretrained(QUIZ_MODEL_PATH)
summary_tokenizer = AutoTokenizer.from_pretrained(SUMMARY_MODEL_PATH)

print(f"Quiz pad_token: {quiz_tokenizer.pad_token}, pad_token_id: {quiz_tokenizer.pad_token_id}")
print(f"Summary pad_token: {summary_tokenizer.pad_token}, pad_token_id: {summary_tokenizer.pad_token_id}")

