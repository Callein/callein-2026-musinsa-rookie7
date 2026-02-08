# 수강신청 시스템 (Course Registration System)

대학교 수강신청 시스템 API 프로젝트입니다. 학생, 교수, 관리자가 사용할 수 있는 기능을 제공하며, 과목 조회, 수강신청, 성적 관리 등의 기능을 포함합니다.

## 🚀 실행 방법

### 환경 설정

이 프로젝트는 Python 3.10+ 환경에서 실행됩니다. 또한 PostgreSQL 데이터베이스가 필요합니다.

1. **저장소 클론 및 디렉토리 이동**
   ```bash
   # 저장소를 클론합니다.
   git clone <repository_url>
   cd callein-2026-musinsa-rookie7
   ```

2. **가상환경 생성 및 활성화**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

3. **의존성 설치**
   ```bash
   pip install -r requirements.txt
   ```

4. **데이터베이스 실행 (Docker)**
   ```bash
   docker-compose up -d
   ```

### 실행

데이터베이스가 실행 중인 상태에서 아래 명령어로 서버를 시작합니다.

```bash
# 개발 모드로 실행 (코드 변경 시 자동 재시작)
uvicorn src.main:app --reload

# 또는 python 명령어로 실행
python src/main.py
```

서버가 실행되면 [http://localhost:8000/docs](http://localhost:8000/docs) 에서 API 문서를 확인할 수 있습니다.

### 테스트

```bash
# 전체 테스트 실행
pytest

# 커버리지 포함 실행
pytest --cov=src
```

## 📁 프로젝트 구조

```
├── src/
│   ├── main.py           # 애플리케이션 진입점 (FastAPI App)
│   ├── config.py         # 설정 관리
│   ├── database.py       # 데이터베이스 연결 및 세션 관리
│   ├── dependencies.py   # 의존성 주입 (Dependency Injection)
│   ├── models/           # SQLAlchemy ORM 모델
│   ├── routers/          # API 엔드포인트 라우터
│   ├── schemas/          # Pydantic 데이터 검증 스키마
│   ├── services/         # 비즈니스 로직
│   └── utils/            # 유틸리티 함수
├── tests/                # 테스트 코드
├── requirements.txt      # 프로젝트 의존성 목록
├── docker-compose.yml    # 데이터베이스(PostgreSQL) 실행 설정
└── README.md             # 프로젝트 문서
```

## 📖 API 문서
| 문서 종류 | URL |
|-----------|-----|
| Swagger UI | [http://localhost:8000/docs](http://localhost:8000/docs) |
| ReDoc | [http://localhost:8000/redoc](http://localhost:8000/redoc) |
| API 문서 | [docs/API.md](./docs/API.md) |

### 주요 기능
- **인증**: JWT 기반 로그인
- **학생**: 목록 및 상세 조회
- **교수**: 목록 및 상세 조회
- **강좌**: 목록 및 상세 조회 (시간표 포함)
- **수강신청**: 신청, 취소, 내 시간표 조회 (동시성 제어 적용)

## 🔧 주요 기능

- **회원가입 및 인증**: JWT 기반 인증 (Access/Refresh Token), 비밀번호 해싱 (Bcrypt).
- **수강신청**: 동시성 제어가 적용된 수강신청 기능.
- **과목 관리**: 과목 등록, 수정, 조회 기능.
- **사용자 역할**: 학생, 교수, 관리자 역할 구분 및 권한 관리.
- **데이터베이스**: PostgreSQL, SQLAlchemy(Async) 사용.

## 📝 의사결정 기록

프로젝트 진행 과정에서 발생한 주요 기술적 의사결정과 트레이드오프에 대한 기록입니다.

### 1. [데이터베이스 선택]
- **상황**: 동시성 제어가 핵심인 수강신청 시스템 구축
- **선택지**:
    - A: SQLite (가볍지만 동시성 제어 제한적)
    - B: In-Memory (빠르지만 데이터 지속성 없음)
    - C: **PostgreSQL** (강력한 잠금 기능 제공)
- **결정**: **PostgreSQL** 선택
- **이유**: `SELECT FOR UPDATE`를 통한 행 레벨 잠금(Row-level Locking)을 사용하여, "정원 1명 남은 강좌에 100명 동시 신청 시 정확히 1명만 성공"이라는 핵심 요구사항을 가장 안정적으로 구현할 수 있기 때문입니다.

### 2. [인증 방식]
- **상황**: 사용자 인증 및 인가 처리
- **선택지**:
    - A: Session 기반 (서버 상태 저장 필요)
    - B: **JWT 기반** (Stateless, 확장성 용이)
    - C: 단순 학번 전달 (보안 취약)
- **결정**: **JWT** 선택
- **이유**: REST API의 Stateless 특성을 유지하고, 프론트엔드와의 연동 표준(Bearer Token)을 준수하기 위함입니다.

### 3. [동시성 제어 전략]
- **상황**: 강좌 정원 초과 방지
- **선택지**:
    - A: 낙관적 락 (Optimistic Lock) - 충돌 시 재시도 필요, 사용자 경험 저하 가능성
    - B: **비관적 락 (Pessimistic Lock)** - 데이터 조회 시점부터 잠금
    - C: Redis 분산 락 - 인프라 복잡도 증가
- **결정**: **비관적 락 (`SELECT FOR UPDATE`)** 선택
- **이유**: 수강신청은 충돌 빈도가 매우 높은 "핫스팟" 영역이므로, 데이터 정합성을 가장 확실하게 보장하는 비관적 락이 적합하다고 판단했습니다. 또한 데드락 방지를 위해 한 번에 하나의 강좌만 신청하도록 API를 설계했습니다.

### 4. [테스트 전략]
- **상황**: 신뢰성 있는 테스트 환경 구축
- **선택지**:
    - A: 공유 DB 사용 (테스트 간 간섭 발생)
    - B: **Transaction Rollback & Fixture Isolation**
- **결정**: **Transaction Rollback 패턴** 및 **격리된 Fixture** 사용
- **이유**: 각 테스트가 독립적으로 실행되도록 보장하고, 특히 동시성 테스트(`test_concurrency.py`)에서는 실제 운영 환경과 유사하게 별도의 DB 커넥션 풀을 사용하여 100명 동시 접속 상황을 검증했습니다.
