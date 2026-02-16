## **어떤 개발 프로젝트를 해보셨나요?**

```markdown
저는 AI 도구(Gemini, Antigravity, ChatGPT등)를 개발 프로세스 전반에 통합하여 생산성을 극대화하고, 이를 통해 확보한 시간을 비즈니스 로직 최적화와 아키텍처 고도화에 투자합니다. 적극적인 AI와의 협업을 통해 실제 서비스 개발에 적용해 유의미한 성과를 낸 3가지 사례입니다.

(상세 내용은 첨부된 이력서와 포트폴리오를 참고 부탁드립니다.)

1. RAGvertise: AI 광고 포트폴리오 추천 엔진 (Back-end / AI)
- 핵심 기술: Python(FastAPI), FAISS, Vector Search
- 성과: KTL(한국산업기술시험원) 공식 성능 인증 획득.
- 문제 해결: 5개의 벡터 인덱스를 병합하는 과정에서 발생한 연산 비용 문제를 가중치 선 반영 알고리즘으로 해결하여, 연산 비용 75% 절감 및 응답 속도 0.25s를 달성했습니다.
- AI 활용: LLM을 활용해 복잡한 벡터 연산 로직의 초안을 빠르게 구현하고, 저는 엣지 케이스 처리와 성능 튜닝에 집중했습니다.

2. Handong Feed: 교내 정보 큐레이션 플랫폼 (Back-end / AI)
- 핵심 기술: Java(Spring Boot), Python(FastAPI), Annoy, Docker, GitHub Actions
- 성과: 실사용자 대상 교내 정보 통합 서비스 운영, 중복 데이터 70% 자동 압축.
- 문제 해결: 무신사와 유사한 Polyglot 환경(SpringBoot - Core, Python - AI Worker)을 구축하여 시스템 안정성과 AI/벡터 연산 효율성을 동시에 확보했습니다. TF-IDF와 Annoy(Vector Index, ANN)를 결합하여 정보 밀도를 획기적으로 높였습니다.

3. CMS: 비동기 분산 미디어 엔진 (Back-end / Infra)
- 핵심 기술: Spring Boot, RabbitMQ, FFmpeg, Python, Celery
- 성과: 메세지 큐를 이용한 480p/1080p 동시 변환 파이프라인 구축 및 보안 스트리밍 구현
- 문제 해결: RabbitMQ를 도입하여 트래픽 폭주 시에도 서버가 죽지 않도록 대기열을 만들고, 업로드 실패 시 스토리지에 고아 파일이 남지 않도록 데이터 정합성 로직을 추가했습니다.

저는 위 프로젝트들을 통해 단순한 기능 구현을 넘어, 시스템 효율성을 높이는 엔지니어링에 집중해 왔습니다. 무신사에서도 AI를 동료 삼아 빠르고 견고하게 성장하겠습니다.
```

## **주로 어떤 기술을 사용하셨나요?**

```markdown
[Backend]
- Java / Spring Boot
- Python / FastAPI, Django

[AI Engineering & Data]
- Vector Search: FAISS, Annoy
- LLM / Embedding: LangChain, Ollama, Hugging Face
- Data Processing: Pandas, NumPy

[Infra & DevOps]
- Message Queue: RabbitMQ
- DevOps: Docker, GitHub Actions (CI/CD), Kubernetes (기초)
- Database: MariaDB, MySQL, MinIO(S3)

[Tools & Productivity]
- AI IDE: Antigravity, GitHub Copilot
- Testing: Puppeteer, Selenium
```

## **어떤 AI 도구를 사용해보셨나요?**

```markdown
Google Antigravity
- 활용: LADS(교내 공항 안전 관리 대시보드 프로젝트) 프로젝트의 프론트엔드/백엔드 전 과정을 AI 에이전트로 구축하여 클라이언트(교내 공항 안전 관리 직원)에게 성공적으로 인도.
- 수준: AI 에이전트를 사용해 풀스택 개발을 주도하고, 생성된 코드의 정합성을 검증/보완하여 상용 수준의 결과물 도출.

Gemini (능숙)
- 활용: 단순 코딩 보조를 넘어 '페어 프로그래밍' 파트너로 활용. 아키텍처 설계 시 엣지 케이스 발굴 및 최적화 수행.

Prompt Engineering
- 활용: RAGvertise 및 Handong Feed 서비스 개발 시, LLM의 답변 품질을 제어하는 시스템 프롬프트(Persona, JSON 포맷 강제 등) 설계 및 최적화.
```