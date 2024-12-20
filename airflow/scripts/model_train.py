import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

# 데이터 로드
def load_data(data_path):
    import json
    with open(data_path, 'r') as f:
        return json.load(f)

data = load_data("/opt/airflow/data/training_data.json")

# 모델 및 토크나이저 준비
tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")
model = AutoModelForSequenceClassification.from_pretrained("bert-base-uncased")

# 데이터 전처리 및 학습 준비
inputs = tokenizer([item['text'] for item in data], padding=True, truncation=True, return_tensors="pt")
labels = torch.tensor([item['label'] for item in data])

# 학습 로직 (초안)
optimizer = torch.optim.AdamW(model.parameters(), lr=5e-5)
model.train()
for epoch in range(3):
    outputs = model(**inputs, labels=labels)
    loss = outputs.loss
    loss.backward()
    optimizer.step()
    optimizer.zero_grad()
