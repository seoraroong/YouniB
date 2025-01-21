## 💡 YouniB: Your University Better, 대학생 학습 플랫폼
<img width="668" alt="화면 캡처 2025-01-01 210933" src="https://github.com/user-attachments/assets/09639740-11d1-4792-ad76-c06e30235f0d" />

### YouniB가 제공하는 기능
- **강의 자료 관리**: 대학생들이 강의 자료 PDF를 강의별로 구조적으로 정리하고 관리할 수 있습니다. 
- **문제 생성 기능**: 강의 자료를 분석해 객관식 및 단답형 문제를 자동으로 생성해 제공합니다.
- **자료 요약 기능**: 강의 자료의 핵심 내용을 요약해 제공함으로써 학습 효율을 높입니다.
- **자기주도 학습**: 매일 제공되는 복습 문제를 풀고 경험치를 얻어 나만의 **유니(Youni)** 를 만들어보세요!
### YouniB 살펴보기
- 시연 영상 YouTube 링크: [YouniB 시연 영상](https://www.youtube.com/watch?v=38F0GuY_x2g)   


## ❓ YouniB는 왜, 누구를 위해 만들어졌나요?
- 중, 고등학생들을 위한 학습 플랫폼은 다양하고 많은 반면, 대학생들을 위한 서비스는 많지 않습니다.
- **YouniB**는 대학생들이 방대한 강의 자료를 효과적으로 활용하고 학습에 집중할 수 있도록 돕기 위해 개발되었습니다.
- 반복적인 강의 자료 정리, 요약 작업, 예상 시험 문제에 대한 고민의 부담을 줄여줍니다.
- 대학생들의 시험 준비, 과제 수행에 필요한 시간과 노력을 절감해 효율적인 학습을 할 수 있도록 설계되었습니다.

## YouniB를 함께 개발한 팀원



| 김설아 | 안도형 | 장석우 | 천세현 |
| --- | --- | --- | --- |
| [GitHub](https://github.com/seoraroong) | [GitHub](https://github.com/andohyung) | [GitHub](https://github.com/sukwoojang) | [GitHub](https://github.com/1000century) |
| **PM** / **데이터 ETL** / **BE** / **FE** | **데이터 ETL** / **QA Modeling** | **데이터 ETL** / **Summary Modeling** | **데이터 ETL** / **QA Modeling** |




## 🛠 YouniB 기술 스택
- Language: Python
- Frontend: HTML/CSS, BootStrap, JavaScript
- Backend: Django, FastAPI, Redis
- NLP: Hugging Face
- Infra: Docker
- DataBase: PostgreSQL

## 데이터셋
- KOCW 생물학 도메인 대학별 강의 자료 PDF
- 수집한 강의 자료 기반 QA 데이터셋 (ChatGPT 활용)
- CNN Daily Mail 요약 데이터셋
- Hugging Face BioQA 데이터셋

## ERD

<img width="533" alt="화면 캡처 2025-01-01 225654" src="https://github.com/user-attachments/assets/b4d52973-8442-4407-9927-aa37c56d6d65" />

## 시스템 아키텍처

YouniB는 **Frontend**, **Backend**, **Database**, 그리고 **LLM 서비스**로 구성된 모듈형 아키텍처를 사용해 개발되었습니다.
<img width="737" alt="image" src="https://github.com/user-attachments/assets/a7e7bfc6-4432-4432-85bd-f2498291f1c5" />
#### Frontend
- **HTML/CSS**, **JavaScript**, **Bootstrap**
  - 직관적인 UI/UX를 구현하기 위해 사용되었습니다.
- 사용자는 웹 인터페이스를 통해 강의 자료를 업로드하거나 요약/퀴즈 생성 결과를 확인할 수 있습니다.
- KT Cloud 상에서 호스팅되며, Docker-compose를 통해 배포 및 관리할 수 있도록 구축했습니다.

 #### Backend
- **Django**
  - 사용자의 요청을 처리하고 데이터베이스와의 상호작용을 담당합니다.
  - 강의 자료 업로드, 요약 요청 상태 관리, 퀴즈 생성 데이터 저장 등의 기능을 수행합니다.
- **FastAPI**
  - 요약 및 퀴즈 생성 모델을 서빙하기 위한 프레임워크입니다.
  - PDF 전처리, 모델 추론 (요약/퀴즈 생성) 작업을 처리합니다.

#### Database
- **PostgreSQL**
  - 강의 자료, 요약 결과, 퀴즈 데이터, 사용자 정보 등 구조화된 데이터를 관리합니다.
 
#### LLM 서비스
- **Fine-tuned LLaMA 3.1 8B**
  - 요약 및 퀴즈 생성을 위한 언어 모델로 사용되었습니다.
  - FastAPI를 통해 추론 작업이 실행되며, 백엔드 서버와 통신해 결과를 반환합니다.
 
## 서비스 플로우
YouniB의 주요 기능은 **PDF 강의 자료 업로드**, **요약 생성**, **퀴즈 생성 및 복습 문제 제공** 입니다. 
<img width="915" alt="KakaoTalk_20241226_175024013" src="https://github.com/user-attachments/assets/f7a8a3a2-fd42-480f-9d96-0eed155193a4" />

- (1) PDF 강의 자료 업로드
  - 사용자가 웹 인터페이스르 통해 PDF 파일을 업로드하면, Django 서버가 파일을 수신하고 데이터베이스에 해당 정보를 저장합니다.
    - **summary_status**는 초기 상태로 "pending"으로 설정됩니다.
  - 파일은 **Preprocess Server**로 전달되어 텍스트 추출과 Sliding Window 방식을 통한 청크 처리를 수행합니다.

- (2) 요약 및 퀴즈 생성
  - 전처리된 데이터는 **Inference Server**로 전달됩니다.
    - 퀴즈 생성 모델과 요약 생성 모델이 순차적으로 Load되어 각각의 태스크를 수행하고, 결과를 JSON 형식으로 반환합니다.
    - 결과는 Django 서버로 전송되어 데이터베이스에 저장됩니다.
   
- (3) 실시간 알림 및 결과 제공
  - 요약/퀴즈 생성 완료 시, **Redis Message Broker**를 통해 WebSocket 서버가 알림을 사용자에게 전송합니다.
  - 사용자는 생성된 요약 및 퀴즈 데이터를 웹 인터페이스에서 확인할 수 있습니다.
 
<img width="737" alt="화면 캡처 2025-01-01 225940" src="https://github.com/user-attachments/assets/94328261-bfd2-4c65-8366-8363a4ebdfd1" />

- (4) 퀴즈 풀이 및 피드백
  - 사용자가 퀴즈를 풀고 제출하면 **Quiz 테이블**과 제출 데이터를 비교해 점수를 계산합니다.
  - 오답에 대해 **오늘의 문제**를 하루 단위로 제공해 사용자가 복습할 수 있도록 합니다. 

## 데이터 수집

- 프로젝트 기획 단계에서 **대학교 내 모든 전공에 대한 강의자료**를 수집하고 파인튜닝하는 것이 어렵다고 판단해 **생물학(Biology)** 도메인을 선정했습니다.
  - 생물학 도메인은 다른 공학 관련 전공에 비해 수식이 적고, **이론과 지식 기반**의 성격이 강하기 때문에 프로젝트 진행에 어려움이 없을 것으로 판단하고 결정했습니다.    
- KOCW에서 생물학 도메인의 대학 강의 자료 PDF를 다운로드 받아 Google Drive에 저장 후 전처리를 진행했습니다.

## 데이터 전처리

- MinerU 라이브러리를 활용해 강의 자료 PDF에서 텍스트만 추출해 json 파일로 저장했습니다.
  
## 데이터 후처리

- 불필요한 문자나 기호 등을 정규식으로 제거해 정제하는 작업을 진행했습니다.

## 데이터셋 생성

- 후처리한 강의 자료 데이터를 ChatGPT에 입력으로 넣고, 일관된 프롬프트를 제공해 약 5000개의 QA 데이터셋을 구축했습니다. 

## 후보 모델 선정

### 생물학 도메인 지식 평가
- Hugging Face의 Leader Board를 참고해 다음과 같은 후보 모델을 선정했습니다.
  - LLaMA3 8B, QWEN 7B, Mistral 7B
- Hugging Face의 BioQA 데이터셋 5000개 중 1000개를 test 데이터셋으로 분리 후 각각의 모델이 몇 개의 정답을 맞추는지 평가했습니다.


<details><summary>프롬프트 1
</summary>


```
input_text = f'Question: {Question}\n\n Option: {"\n".join(i for i in options)}\n{Answer}
```

</details>

  
| QWEN Instruct | Mistral Instruct | LlaMA Instruct |
| --- | --- | --- |
| 256/1000 | 256/1000 | 280 / 1000 |

프롬프트 1은 Answer와 Option이 명확하게 분리되어 있지 않은 상태입니다.


<details><summary>프롬프트 2
</summary>


```
def __getitem__(self, idx):
  sample = self.dataset[idx]

  input_text = f"Question: {sample['question']}\n\nOptions:\n"
  for option in sample['options']:
    input_text += f"{option}\n"
  input_text += '\nAnswers: '

  target_text = sample['answer']
  combined_text = input_text + target_text
```

</details>

| QWEN Instruct | Mistral Instruct | LlaMA Instruct |
| --- | --- | --- |
| 754/1000 | 758/1000 | 760/1000 |

프롬프트 2는 Answer와 Option을 명확하게 분리하도록 수정한 상태입니다.

위 실험을 통해 **모델에 따른 성능 차이**가 존재함을 확인할 수 있습니다. 그러나 동일한 모델이라도 **프롬프트**에 따라 성능 차이가 확연하다는 사실 또한 알 수 있습니다. 

## 파인튜닝 실험 설계

BioQA 데이터셋을 활용해 선정한 LLaMA 3.1 8B을 "문제 생성", "요약 생성" 태스크에 맞게 파인튜닝하기 위한 전략은 다음과 같습니다.

#### Instruct 모델 사용
- 특정 도메인에 특화
- 사용자가 의도하는 작업에 부합
- **Instruct 모델은 사용자의 명령이나 지시에 초점을 맞춰 명확하고 간결한 답변을 제공하도록 학습**

#### 양자화
- 메모리 사용량 감소
- 추론 속도 향상
- 성능 손실 최소화
- **제한된 자원에서 큰 사이즈의 LLM 모델을 온전히 활용하기에는 한계가 존재함**
- **모델을 최대한 손상시키지 않으면서 모델의 크기를 줄여 메모리를 조절하고 계산 비용을 낮추기 위해 활용**

#### 파인튜닝
- 파인튜닝 비용 및 리소스 절감
- 멀티 태스크 특화
- **프롬프트 위주의 파인튜닝**

### 1. 문제 생성 태스크
- 객관식 3300 문제, 단답형 3300 문제, 총 6600개의 데이터셋을 통한 모델 학습
- 학습되지 않은 새로운 문제들을 프롬프트 상에 예시로 추가하는 One-Shot, Few-Shot 기법으로 파인 튜닝 진행 및 추론 결과 확인


<details><summary>실험 결과 - 프롬프트 엔지니어링
</summary>

- Few-Shot (예시 1, 2, 4개)
- 프롬프트 구조 배치 (Context + Instruct, Instruct + Context)


| **Method**           | **ROUGE-1 Precision** | **ROUGE-2 Precision** | **ROUGE-L Precision** | **Hallucination (1~0)** |
|-----------------------|-----------------------|-----------------------|-----------------------|-------------------------|
| **Few Shot 1**        | **0.753**            | **0.452**            | **0.586**            | **0.212**              |
| Few Shot 2           | 0.715                | 0.424                | 0.564                | 0.241                  |
| Few Shot 4           | 0.660                | 0.374                | 0.522                | 0.350                  |
| Context + Instruct   | 0.740                | 0.412                | 0.564                | 0.253                  |
| **Instruct + Context**| **0.748**            | **0.439**            | **0.576**            | **0.182**              |


- Few-Shot 예시 개수는 1개가 적절함을 확인할 수 있습니다.
- 지시 사항을 먼저 알려주고 문맥을 제공하는 것이 더 좋은 결과를 보인다는 사실을 확인할 수 있습니다. 
- Few-Shot 여부로 결과에 큰 차이가 나지 않았기에 토큰 수가 적은 **Instruct + Context** 방안을 채택했습니다

</details>


<details><summary>실험 결과 - 하이퍼파라미터 튜닝
</summary>

- 다음 세 가지 하이퍼파라미터에 대해 모델 성능과 hallucination 수준을 분석했습니다.
  - **LoRA Parameters**: LoRA 구성 설정 (LoRA1, LoRA2, LoRA3)
  - **Batch Size**: 4, 7, 10
  - **Learning Rate**: 1e-5, 2e-5, 1e-4

// 이미지 첨부 //

#### 분석 결과
(1) **LoRA Parameters**
- ROUGE-2 Precision: LoRA 파라미터가 증가함에 따라 성능이 미세하게 개선되었습니다.
  - LoRA1: 0.432 -> LoRA3: 0.440
- Hallucination: LoRA3 설정에서 가장 낮은 값 (0.180)을 보여, 잘못된 정보 생성을 억제하는 효과를 확인했습니다.
  - LoRA1: 0.141 -> LoRA3: 0.180

(2) **Batch Size**
- ROUGE-2 Precision: 배치 크기가 증가할수록 성능이 미세하게 감소하는 것을 확인했습니다.
  - Batch4: 0.453 -> Batch 10: 0.432
- Hallucination: 배치 크기 증가 시 잘못된 정보 생성이 감소하는 경향을 확인했습니다.
  - Batch4: 0.211 -> Batch 10: 0.141

(3) **Learning Rate**
- ROUGE-2 Precision: 낮은 학습률(1e-5)에서 가장 높은 성능 (0.458)을 보임을 확인했습니다.
- Hallucination: 학습률이 감소하면 잘못된 정보 생성 또한 감소하는 경향을 확인했습니다.
  - 1e-5: 0.219 -> 1e-4: 0.132

</details>

### 2. 요약 태스크
- 생물학 관련 요약 데이터셋 확보의 어려움으로 인해 도메인 지식을 가지고 있는 Base 모델에 도메인과 관련 없는 일반적인 요약 데이터셋으로 **모델의 도메인 지식은 유지**하며 특정 태스크의 성능을 끌어올릴 수 있는 방안을 고려했습니다.
- 모델 선정 과정에서 도메인 지식이 검증된 LLaMA 모델에 CNN (신문) 요약 데이터셋을 활용해 일반적인 요약 태스크의 포괄적 특성을 모델에 학습했습니다.


<details><summary>실험 결과
</summary>

#### 평가 방법
- ROUGE 평가 지표: 요약 성능을 평가하기 위해 ROUGE-1, ROUGE-2, ROUGE-L을 사용했습니다.
  - ROUGE-1: 단일 단어 매칭
  - ROUGE-2: 2-gram 매칭
  - ROUGE-L: 긴 공통 서브 시퀀스 매칭

- 정성적 평가와 정량적 평가
  - 정성적 평가 (Human Score)외에도 정량적 평가를 위해 ROUGE 점수를 사용했습니다.
  - 결론적으로, Human Score 대비 ROUGE 성능에서 눈에 띄는 차이는 확인할 수 없었습니다.

#### 결과 분석
(1) ROUGE-1 성능
- 그래프를 통해 샘플 간 성능 변화를 확인했습니다.
- 각 데이터셋 간 성능 차이는 크지 않았으며, 특정 샘플에서는 비슷한 성능을 기록했습니다. 

(2) ROUGE-2 성능
- ROUGE-2는 짧은 n-gram을 활용한 평가로, 샘플에 따라 큰 변동성을 확인할 수 있습니다.
- 특정 데이터셋 (ft_df3)은 다른 데이터셋에 비해 성능이 다소 낮은 점을 확인할 수 있습니다.

(3) ROUGE-L 성능
- 긴 공통 서브 시퀀스를 활용한 ROUGE-L 지표에서도 비슷한 경향을 보였습니다.
- 샘플에 따라 성능이 변동하며, 일부 데이터셋은 안정적인 성능을 보임을 확인할 수 있습니다. 

**결론적으로 ROUGE 평가 지표는 정량적 평가의 기준으로는 적합하나, Human Score를 완벽히 대체하지는 못한다는 결론을 내렸습니다.**

// 이미지 첨부 //

- PT (Pre-trained Model)
  - 기본 LLaMA 모델을 사용해 추론 진행
- FT1 (Fine-Tuning 1)
  - 모델의 기존 성능을 유지하기 위해 낮은 학습률과 에폭 수 설정
- FT2 (Fine-Tuning 2)
  - FT1의 결과에서 성능 향상을 확인
  - 그러나 성능 향상이 제한적이었기 때문에 학습률과 데이터 수를 증가시켜 재학습 진행
- FT3 (Fine-Tuning 3)
  - FT2 결과를 기반으로 추가 학습 진행
  - FT2를 베이스로 학습 자원을 대폭 투입해 성능을 극대화

#### Human Score
- 정성적 평가 기준으로 사용했습니다.
- 평가 기준
  - Hallucination 여부: 잘못된 정보 생성 여부 (10점 만점)
  - 주요 정보 포함 여부: 중요한 정보가 포함되어 있는지 여부 (10점 만점)
  - 간결함: 요약의 간결성과 효율성 (10점 만점)

#### 결과 분석
- FT1 -> FT2 -> FT3 으로 진행할 수록 Human Score가 지속적으로 상승함을 알 수 있습니다.
- FT2에서 학습 데이터와 학습률 조정을 통해 성능이 향상되었으나, FT3에서 대규모 학습 자원을 투입한 결과 더 큰 성능 향상이 이루어졌음을 확인할 수 있습니다. 
</details>

## 기술적 도전과 해결 방안

## 향후 개선 방향

## 사용자 시나리오



