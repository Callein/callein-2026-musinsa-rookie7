# 2차 코딩테스트 기술 회고 보고서

## 대학교 수강신청 시스템 — 설계 의도와 엔지니어링 판단의 기록

---

## 1. 핵심 문제 정의

### 1.1 본질: 재고 차감 문제의 변형

수강신청 시스템의 핵심 도전은 단순한 CRUD가 아닙니다. **"정원이 1명 남은 강좌에 100명이 동시에 신청하면, 정확히 1명만 성공해야 한다"** — 이것은 전형적인 재고 차감(inventory decrement) 문제이며, 이커머스의 한정 수량 상품 구매와 동일한 구조를 가집니다.

문제를 분해하면 다음과 같습니다:

| 제약사항 | 동시성 관련 여부 | 위험도 |
|----------|:---:|:---:|
| 정원 초과 방지 | O | 치명적 — 데이터 정합성 파괴 |
| 최대 18학점 제한 | △ | 동일 학생의 동시 요청 시 race condition 가능 |
| 시간표 충돌 방지 | △ | 동일 학생의 동시 요청 시 phantom read 가능 |
| 동일 강좌 중복 방지 | O | DB UNIQUE 제약으로 해결 가능 |

핵심 통찰은, 이 네 가지 제약사항이 **모두 하나의 트랜잭션 안에서 원자적으로 검증되어야 한다**는 점입니다. 검증과 쓰기 사이에 시간 간격이 존재하면, 그 틈으로 정합성이 깨집니다.

### 1.2 비즈니스 맥락

10,000명의 학생, 500개 이상의 강좌, 12개 학과 — 실제 대학의 수강신청 기간을 시뮬레이션합니다. 수강신청 시작 시점에는 인기 강좌에 수백 명이 동시에 몰리는 것이 정상이며, 이 시나리오에서 **단 한 건의 초과 등록도 허용할 수 없습니다.**

---

## 2. AI Native 협업 프로세스

### 2.1 CLAUDE.md를 통한 에이전트 페르소나 관리

이 프로젝트에서 AI는 단순한 코드 생성기가 아니라, **일관된 엔지니어링 원칙을 공유하는 페어 프로그래밍 파트너**로 기능했습니다. 이를 가능하게 한 것이 `CLAUDE.md`와 `.claude/rules/` 디렉토리입니다.

**CLAUDE.md의 역할:**
- 프로젝트의 기술 스택과 아키텍처를 선언적으로 정의
- 코딩 컨벤션(불변성 패턴, 타입 힌트, 한국어 에러 메시지)을 명시
- API 응답 포맷을 표준화하여 AI가 생성하는 모든 엔드포인트가 동일한 구조를 따르도록 제약
- 커밋 메시지 형식(`type(scope): description`)을 규정하여 Git 히스토리의 일관성 확보

**7개의 Rules 파일을 통한 세분화된 지침:**

| 파일 | 제어 영역 |
|------|----------|
| `coding-style.md` | 불변성 패턴, 타입 힌트, 에러 처리 방식 |
| `git-workflow.md` | 브랜치 전략, 커밋 메시지 형식 |
| `testing.md` | TDD 워크플로우, 80%+ 커버리지 목표 |
| `performance.md` | 모델 선택 전략, 컨텍스트 윈도우 관리 |
| `agents.md` | 에이전트 오케스트레이션(planner, tdd-guide, code-reviewer) |
| `security.md` | 시크릿 관리, 입력 검증 원칙 |
| `project-structure.md` | 디렉토리 구조, 네이밍 규칙 |

이 구조의 핵심 가치는 **재현 가능성**입니다. 다른 개발자가 동일한 CLAUDE.md를 사용하면, AI가 동일한 코딩 스타일과 아키텍처 판단을 따릅니다. 이것은 팀 단위의 AI 활용에서 품질 편차를 줄이는 실질적인 방법론입니다.

### 2.2 설계 단계에서의 AI 협업: SELECT FOR UPDATE 도출 과정

`SELECT FOR UPDATE`라는 최종 결정에 도달하기까지, AI와의 협업은 다음과 같은 구조화된 논의를 거쳤습니다.

**Phase 1 — 문제 구조화:**
요구사항 문서를 분석하여 명시적 요구사항 9개와 암묵적 요구사항 7개를 도출했습니다. 특히 "수강신청 단위를 한 번에 한 과목으로 제한한다"는 암묵적 요구사항(A7)은, 이후 데드락 방지 전략의 기반이 됩니다.

**Phase 2 — 대안 비교 분석:**
네 가지 동시성 제어 전략을 체계적으로 비교했습니다:
- **낙관적 락**: 충돌 시 재시도가 필요한데, 수강신청은 본질적으로 충돌 빈도가 극도로 높아 재시도 폭주(retry storm)가 발생합니다.
- **Application Lock(asyncio.Lock)**: 단일 프로세스에서만 유효하여 수평 확장이 불가합니다.
- **Redis 분산 락**: 추가 인프라가 필요하고, 락 해제 실패 시 장애 전파 위험이 있습니다.
- **SELECT FOR UPDATE**: DB 레벨에서 보장되며, 단일 행 잠금으로 데드락 위험이 없습니다.

**Phase 3 — 격리 수준 결정:**
Serializable까지 올릴 필요가 있는지 논의했습니다. 결론은 **Read Committed + 행 잠금**이 충분하다는 것이었습니다. `SELECT FOR UPDATE`는 잠금 획득 시점에 최신 커밋 데이터를 읽으므로, 비용이 높은 Serializable 없이도 정합성을 보장합니다.

이 과정에서 AI의 가치는 "정답을 알려주는 것"이 아니라, **각 선택지의 트레이드오프를 체계적으로 나열하여 근거 있는 의사결정을 가능하게 한 것**입니다.

---

## 3. 기술적 의사결정 및 근거

### 3.1 왜 PostgreSQL 비관적 락인가

**낙관적 락과의 비교:**

```
낙관적 락 (Optimistic Locking)
┌─────────────────────────────────────┐
│ TX-A: SELECT enrolled, version ...  │
│ TX-B: SELECT enrolled, version ...  │  ← 두 트랜잭션 모두 같은 값을 읽음
│ TX-A: UPDATE ... WHERE version = v  │  ← 성공
│ TX-B: UPDATE ... WHERE version = v  │  ← 실패 → 재시도 필요
└─────────────────────────────────────┘

비관적 락 (Pessimistic Locking)
┌─────────────────────────────────────┐
│ TX-A: SELECT ... FOR UPDATE         │  ← 행 잠금 획득
│ TX-B: SELECT ... FOR UPDATE         │  ← TX-A 완료까지 대기
│ TX-A: UPDATE + COMMIT               │  ← 잠금 해제
│ TX-B: 최신 데이터로 읽기 → 검증          │  ← 정원 초과 시 즉시 실패
└─────────────────────────────────────┘
```

수강신청 시나리오에서 낙관적 락의 문제는 명확합니다:
1. **재시도 폭주**: 100명이 동시에 접근하면, 99명이 실패하고 재시도합니다. 재시도한 99명 중 또 98명이 실패합니다. 이 연쇄가 시스템 부하를 기하급수적으로 증가시킵니다.
2. **사용자 경험 저하**: 클라이언트에 재시도 로직을 구현해야 하며, 사용자는 "신청 실패 → 다시 시도해주세요" 메시지를 반복적으로 보게 됩니다.
3. **공정성 부재**: 먼저 신청한 사용자가 아니라, 운 좋게 충돌을 피한 사용자가 성공합니다.

비관적 락은 이 세 가지 문제를 근본적으로 해결합니다. 대기 시간이 발생하지만, 대기 후에는 확정적인 결과(성공 또는 실패)를 받습니다.

**데드락 방지 설계:**
수강신청 API를 "한 번에 한 과목"으로 제한한 것은 의도적인 설계입니다. 단일 트랜잭션에서 하나의 Course 행만 잠그므로, 순환 대기(circular wait)가 물리적으로 불가능합니다. 이것은 API 설계 수준에서 데드락을 원천 차단하는 접근입니다.

**SELECT FOR UPDATE vs Serializable**

| **구분** | **SELECT FOR UPDATE (비관적 락)** | **Serializable (격리 수준)** |
| --- | --- | --- |
| **방식** | **"줄 서세요!"** (명시적으로 딱 막음) | **"일단 하세요, 나중에 검사함"** (사후 검사) |
| **충돌 시** | 앞사람 끝날 때까지 **기동차게 대기**함 | **에러 발생 및 트랜잭션 취소** (다시 시작해야 함) |
| **범위** | 내가 `FOR UPDATE`로 찍은 **그 행만** | 트랜잭션이 건드린 **모든 데이터와 그 범위** |
| **장점** | 데이터 정합성이 확실하고 재시도가 필요 없음 | 이론상 완벽한 격리성 제공 |
| **단점** | 대기 시간(Wait)이 발생함 | 고부하 상황에서 **성공률이 극도로 낮아짐** |

### 3.2 10,000명 데이터 생성 전략

1분 이내에 10,000명의 학생과 500개 이상의 강좌를 생성해야 했습니다. 핵심 전략은 세 가지입니다:

**배치 삽입(Batch Insert):**
학생 데이터를 1,000건 단위로 묶어서 삽입합니다. 10,000건을 개별 INSERT로 처리하면 10,000번의 DB 라운드트립이 발생하지만, 배치 처리하면 10번으로 줄어듭니다.

**결정론적 생성(Deterministic Generation):**
`random.Random(42)` — 고정 시드를 사용하여 동일한 데이터를 재현할 수 있습니다. 이는 디버깅과 테스트에서 결정적인 이점입니다. "학번 20210042의 학생이 왜 특정 상태인지"를 추적할 수 있습니다.

**멱등성(Idempotency):**
서버 시작 시 `departments` 테이블의 레코드 수를 확인하고, 데이터가 이미 존재하면 시드 생성을 스킵합니다. 서버를 몇 번 재시작하든 데이터가 중복되지 않습니다.

**현실적 데이터 모델링:**
한국 성씨 30개 × 이름 50개 조합, 12개 실제 학과명, 학과별 실제 과목명 토큰 목록을 사용했습니다. 교수의 시간표 충돌 방지까지 고려하여, 동일 교수에게 같은 시간대 강좌가 배정되지 않도록 했습니다.

---

## 4. 코드 구조 설계: Router-Service-Model 계층 아키텍처

### 4.1 왜 계층화했는가

```
Request → Router → Service → Model → Database
                      ↓
                  Business Rules
                  (정원 검증, 학점 검증, 시간표 충돌 검증)
```

**Router 계층 (API Controllers):**
HTTP 요청/응답 처리와 의존성 주입만 담당합니다. 비즈니스 로직이 없으므로, FastAPI를 다른 프레임워크로 교체하더라도 서비스 계층은 영향받지 않습니다.

**Service 계층 (Business Logic):**
수강신청의 모든 비즈니스 규칙이 이곳에 집중되어 있습니다. `enrollment_service.py`의 `enroll()` 메서드 하나에서 정원 검증, 학점 검증, 시간표 충돌 검증, 잠금 획득이 모두 일어납니다. 이 설계의 장점은 **테스트 용이성**입니다. Router를 거치지 않고 Service 메서드를 직접 호출하여 단위 테스트할 수 있습니다.

**Model 계층 (Data Schema):**
SQLAlchemy ORM 모델이 데이터베이스 스키마를 정의합니다. `UNIQUE(student_id, course_id)` 같은 제약은 모델 레벨에서 선언되어, 서비스 로직의 버그와 무관하게 데이터 무결성을 보장합니다.

### 4.2 이 분리가 실질적으로 가져온 이점

**동시성 테스트에서의 분리 효과:**
`test_concurrency.py`는 실제 HTTP 요청을 100개 동시에 보내는 통합 테스트입니다. 반면 `test_enrollments.py`는 단일 요청 단위로 비즈니스 규칙을 검증합니다. 계층 분리 덕분에 두 가지 수준의 테스트를 독립적으로 작성할 수 있었습니다.

**의존성 주입 패턴:**
```python
async def create_enrollment(
    body: EnrollmentRequest,
    student: Student = Depends(get_current_student),  # JWT 인증
    db: AsyncSession = Depends(get_db),               # DB 세션
):
```
FastAPI의 `Depends`를 통해 인증과 DB 세션이 주입됩니다. 테스트에서는 이 의존성을 오버라이드하여, 실제 JWT 발급 없이도 인증된 요청을 시뮬레이션할 수 있습니다.

---

## 5. 검증: 동시성 테스트의 설계

단순히 "코드를 작성했다"가 아니라, **"정합성이 보장됨을 증명했다"**가 이 프로젝트의 핵심 산출물입니다.

```python
# test_concurrency.py 핵심 로직
# 정원 1명인 강좌에 100명이 동시 신청
responses = await asyncio.gather(*[
    enroll(student_token, course_id) for student_token in tokens[:100]
])

successes = [r for r in responses if r.status_code == 201]
conflicts = [r for r in responses if r.status_code == 409]

assert len(successes) == 1   # 정확히 1명만 성공
assert len(conflicts) == 99  # 나머지 99명은 충돌
```

테스트 인프라도 운영 환경을 모사했습니다:
- **커넥션 풀**: `pool_size=20, max_overflow=20`으로 실제 부하 시뮬레이션
- **100개 독립 토큰**: 각 학생이 개별 JWT를 가지고 동시에 요청
- **DB 상태 검증**: 응답 코드뿐 아니라, 데이터베이스의 `enrolled` 값이 정확히 1인지까지 확인

---

## 6. 셀프 피드백: 트레이드오프와 개선 가능성

### 6.1 현재 설계의 트레이드오프

**단일 서버 가정:**
현재 `SELECT FOR UPDATE`는 단일 PostgreSQL 인스턴스에서 완벽하게 동작합니다. 하지만 서버를 수평 확장하더라도, 동일한 DB를 바라보는 한 이 전략은 유효합니다. 진정한 한계는 **DB 자체가 분산되는 시점**에서 발생합니다.

**bcrypt 해싱 비용:**
10,000명의 비밀번호를 bcrypt로 해싱하는 것은 시드 데이터 생성 시간의 상당 부분을 차지합니다. 운영 환경에서는 적절하지만, 테스트 데이터 생성에서는 해시 라운드를 낮추는 것이 합리적일 수 있습니다.

**커버리지 58%:**
목표는 80%였으나 달성하지 못했습니다. 파일별 커버리지 리포트를 기준으로 정확한 원인을 분석하면 다음과 같습니다.

```
Name                               Cover   Missing
--------------------------------------------------
enrollment_service.py               25%   44-88, 114-134, 156-181
seed_service.py                      0%   1-214 (전체)
seed_data.py                         0%   5-106 (전체)
routers/professors.py               47%   37-62, 89-100
routers/students.py                 47%   37-63, 90-101
routers/courses.py                  48%   20, 61-79, 106-121
routers/enrollments.py              65%   46-54, 82, 111-117, 136
dependencies.py                     70%   37-38, 44-50
```

**구조적 미달 원인:**

`enrollment_service.py`가 가장 큰 병목입니다. `enroll()`, `cancel()`, `get_schedule()`의 핵심 비즈니스 로직 전체가 미커버 상태입니다. 현재 통합 테스트가 라우터를 통해 내려오는 경로만 검증하는데, 정상 케이스 위주로 작성되어 비즈니스 규칙 분기(학점 초과, 시간표 충돌, 정원 초과의 경계값)를 타지 못하고 있습니다.

`seed_service.py`는 구조적으로 커버가 불가능합니다. 서버 시작 시 멱등성 체크(departments 레코드 존재 확인)에서 이미 스킵되므로, 테스트 환경에서는 실행 경로 자체에 진입하지 않습니다. 이를 테스트하려면 별도의 빈 DB 픽스처가 필요합니다.

`routers/professors.py`, `students.py`, `courses.py`는 페이지네이션 파라미터 조합(`page`, `limit` 경계값)과 존재하지 않는 리소스 조회(404) 케이스가 없습니다.

`dependencies.py`의 미달 라인은 JWT 인증 실패 분기입니다. 만료된 토큰, 서명이 잘못된 토큰, DB에 존재하지 않는 학번의 토큰을 각각 테스트해야 커버됩니다.

**80% 달성을 위한 추가 커버리지 계산:**

```
현재: 569 statements 중 330 covered (58%)
목표: 569 * 0.80 = 456 covered → 126줄 추가 필요
```

우선순위별 추가 테스트 케이스:
1. `enrollment_service.py` — 시간표 충돌(완전 겹침/부분 겹침/맞닿는 경우), 학점 초과, 정원 초과 경계값 (약 40줄)
2. `routers/professors.py`, `students.py` — 페이지네이션 + 404 케이스 (약 34줄)
3. `dependencies.py` — 만료/잘못된 JWT 케이스 (약 6줄)
4. `routers/courses.py` — 필터 파라미터 조합 (약 17줄)

시간 제약 내에서 핵심 경로(인증, 수강신청 CRUD, 100명 동시성)는 모두 검증했으나, 위의 엣지 케이스들이 남은 과제입니다.

### 6.2 시간이 더 있었다면

**분산 환경 확장성:**
- Redis 기반 분산 락(Redlock)과 PostgreSQL Advisory Lock의 비교 검토
- 읽기 전용 레플리카를 활용한 조회 API 부하 분산
- 이벤트 소싱 패턴으로 수강신청 이력의 완전한 감사 추적(audit trail)

**성능 최적화:**
- 인기 강좌의 잔여 정원을 Redis에 캐싱하여, DB 접근 전 사전 필터링
- 수강신청 대기열(queue) 시스템 도입으로 동시 접속 부하 평준화
- 커넥션 풀 크기에 대한 부하 테스트 기반 튜닝

**테스트 강화:**

**(1) Property-based testing으로 시간표 충돌 로직 완전 검증**

현재 `test_enrollments.py`는 시나리오를 손으로 나열합니다(완전 겹침, 부분 겹침, 맞닿는 경우). 하지만 시간표 충돌 함수 `has_schedule_conflict(a_start, a_end, b_start, b_end)`가 정의역 전체에서 성립하는지는 증명하지 못합니다. Hypothesis 라이브러리로 이를 보완할 수 있습니다:

```python
from hypothesis import given, assume, settings
from hypothesis import strategies as st

@given(
    a_start=st.integers(min_value=0, max_value=23),
    a_end=st.integers(min_value=1, max_value=24),
    b_start=st.integers(min_value=0, max_value=23),
    b_end=st.integers(min_value=1, max_value=24),
)
def test_conflict_symmetry(a_start, a_end, b_start, b_end):
    """충돌 여부는 교환법칙이 성립해야 한다."""
    assume(a_start < a_end and b_start < b_end)
    assert has_conflict(a_start, a_end, b_start, b_end) == \
           has_conflict(b_start, b_end, a_start, a_end)

@given(st.integers(0, 23), st.integers(1, 24))
def test_course_never_conflicts_with_itself(start, end):
    """자기 자신과는 항상 충돌해야 한다."""
    assume(start < end)
    assert has_conflict(start, end, start, end) is True
```

Hypothesis는 반례를 찾으면 최소 재현 케이스(shrinking)로 자동 축소합니다. 수작업 테스트가 놓치는 경계 조건(off-by-one)을 수천 번의 무작위 시도로 발견합니다.

**(2) 단위 테스트 격리 강화: Testcontainers**

현재 통합 테스트는 `docker compose`로 띄운 DB를 공유합니다. 테스트 간 상태 오염 위험이 있고, 병렬 실행이 불가합니다. Testcontainers를 사용하면 각 테스트 세션이 독립된 PostgreSQL 컨테이너를 사용합니다:

```python
# conftest.py
from testcontainers.postgres import PostgresContainer

@pytest.fixture(scope="session")
def postgres():
    with PostgresContainer("postgres:16") as pg:
        yield pg.get_connection_url()
```

이 방식은 CI/CD 환경에서 `docker compose up` 없이도 완전한 통합 테스트를 실행할 수 있게 합니다.

**(3) Mutation testing으로 테스트 스위트의 품질 검증**

커버리지 58%는 "어느 코드가 실행됐는가"를 측정하지, "테스트가 버그를 잡는가"를 측정하지 않습니다. `mutmut`으로 뮤테이션 테스트를 적용하면 실제 검출력을 측정할 수 있습니다:

```bash
mutmut run --paths-to-mutate src/services/enrollment_service.py
mutmut results  # 살아남은 뮤턴트 = 테스트가 잡지 못한 버그
```

예를 들어 `enrolled_count >= capacity`를 `enrolled_count > capacity`로 바꾼 뮤턴트가 살아남는다면, 정원 정확히 마지막 1자리를 채우는 경계값 테스트가 없다는 뜻입니다.

**(4) 부하 테스트: k6 시나리오 설계**

단순한 동시 요청 100개를 넘어, 실제 수강신청 기간의 트래픽 패턴을 시뮬레이션합니다:

```javascript
// k6/scenarios/enrollment_rush.js
export const options = {
  scenarios: {
    // 시작 직후 급증 — 인기 강좌 선착순
    enrollment_rush: {
      executor: "ramping-vus",
      startVUs: 0,
      stages: [
        { duration: "10s", target: 1000 },  // 10초 만에 1000명
        { duration: "30s", target: 1000 },  // 30초 유지
        { duration: "10s", target: 0 },
      ],
    },
    // 잔여 정원 조회 — 읽기 부하
    course_polling: {
      executor: "constant-vus",
      vus: 500,
      duration: "50s",
    },
  },
  thresholds: {
    http_req_failed: ["rate<0.01"],          // 오류율 1% 미만
    http_req_duration: ["p(95)<500"],        // 95th percentile 500ms 이하
    "checks{type:enrollment}": ["rate>0.99"], // 수강신청 성공 검증 통과율
  },
};
```

성능 회귀 방지를 위해 임계값(threshold)을 CI 파이프라인에 통합합니다. p95 응답 시간이 500ms를 넘으면 빌드를 실패시킵니다.

**(5) Chaos Engineering: 장애 시나리오별 복원력 검증**

| 장애 시나리오 | 주입 방법 | 검증 지표 |
|---|---|---|
| DB 커넥션 풀 소진 | `pool_size=1`로 강제 제한 | 409 또는 503 응답, 데이터 정합성 유지 |
| 네트워크 지연 (500ms) | `tc netem` 또는 Toxiproxy | 응답 시간 분포, 타임아웃 처리 |
| DB 일시 중단 후 재기동 | `docker pause/unpause postgres` | 재연결 복구 시간, 커넥션 풀 자동 회복 |
| 부분 트랜잭션 실패 | Mock으로 COMMIT 직전 예외 주입 | 롤백 보장, 부분 쓰기 없음 확인 |

Chaos 테스트의 핵심 검증 조건은 단 하나입니다: **어떤 장애 시나리오에서도 `enrolled_count > capacity`인 레코드가 존재하면 안 됩니다.** 모든 카오스 실험 후 `SELECT course_id, enrolled_count, capacity FROM courses WHERE enrolled_count > capacity`의 결과가 빈 셋임을 확인합니다.

**운영 관측성:**
- 구조화된 로깅(structured logging)으로 수강신청 흐름 추적
- Prometheus 메트릭: 수강신청 성공/실패율, 락 대기 시간, API 응답 시간
- 대시보드를 통한 실시간 정원 현황 모니터링

### 6.3 이 프로젝트에서 배운 것

가장 큰 교훈은, **동시성 문제는 코드 레벨이 아니라 설계 레벨에서 해결해야 한다**는 것입니다. "한 번에 한 과목만 신청"이라는 API 설계 결정이, 코드 한 줄 쓰기 전에 데드락 문제를 원천 차단했습니다. 반대로, 이 결정 없이 "여러 과목 동시 신청"을 허용했다면, 아무리 정교한 락 전략을 구현해도 데드락 위험에서 자유로울 수 없었을 것입니다.

AI와의 협업에서 배운 것은, **AI에게 좋은 질문을 하려면 먼저 문제를 정확히 정의해야 한다**는 점입니다. CLAUDE.md에 프로젝트 컨텍스트를 상세히 기술한 것은, 결국 "AI가 더 좋은 판단을 내리도록 하기 위한 투자"였으며, 그 투자는 프로젝트 전반의 일관성으로 돌아왔습니다.

---

## 부록: 프로젝트 수치 요약

| 항목 | 수치 |
|------|------|
| 총 커밋 수 | 40+ |
| 소스 파일 | 20+ (src/) |
| 테스트 파일 | 4 (tests/) |
| 테스트 케이스 | 11 |
| 테스트 커버리지 | 58% |
| 데이터 규모 | 10,000 학생 / 500+ 강좌 / 120 교수 / 12 학과 |
| 동시성 테스트 | 100 동시 요청 → 정확히 1 성공 검증 |
| API 엔드포인트 | 10 |
| AI 규칙 파일 | 7 (.claude/rules/) |
