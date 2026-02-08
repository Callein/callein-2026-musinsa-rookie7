# Claude Code 대화 기록 (Transcript)

> 이 문서는 대학교 수강신청 시스템 개발 과정에서 Claude Code와 나눈 대화를 정리한 것입니다.
> 주요 의사결정 사항, 프롬프트, 그리고 AI의 제안에 대한 피드백을 시간순으로 기록합니다.
> 정리에는 다음 프롬프트가 사용되었습니다.
```
지금까지 우리가 나눈 대화 내용, 특히 주요 의사결정 사항과 내가 입력한 프롬프트들을 정리해서 'prompts/transcript.md' 파일로 만들어줘.
평가자가 볼 수 있도록 가독성 좋게 정리해줘.
```

---

## 1. 프로젝트 시작 및 초기 설계

### 프롬프트 #1: 프로젝트 초기화 요청

```
지금 docs/PROBLEM.md 를 만족하는 백엔드를 구현해야해.
기술스텍은 파이썬, fastAPI로 하자.
포스트맨 대신 브루노를 사용할거고, .github과 templates에 안내사항들 있어.
참고해서 /init 해줘.
```

**Claude의 행동**: PROBLEM.md, .github/, templates/, .bruno/ 등 모든 관련 파일을 읽고 프로젝트 전체 구현 계획을 수립. Plan Mode로 진입하여 7단계 구현 계획서를 작성.

### 의사결정 #1: 데이터베이스 선택

Claude가 SQLite vs PostgreSQL vs 순수 인메모리 3가지 옵션을 제시.

- **나의 선택**: **PostgreSQL**
- **이유**: `SELECT FOR UPDATE`로 강력한 행 레벨 동시성 제어가 가능. 과제의 핵심 요구사항인 "정원 1명 남은 강좌에 100명 동시 신청 → 정확히 1명만 성공"을 DB 레벨에서 보장할 수 있음.

### 의사결정 #2: 인증 방식

Claude가 student_id body 전달 vs JWT vs Header 전달 3가지 옵션을 제시.

- **나의 선택**: **간단한 JWT 토큰**
- **이유**: 실제 프로덕션 환경과 유사한 인증 패턴. 프론트팀 연동 시 표준적인 Bearer 토큰 방식이 자연스러움.

---

## 2. 설계 검토 및 피드백

### 프롬프트 #2: 동시성 제어 보완 지시

```
동시성 제어의 범위 (Deadlock 방지)
학생이 동시에 여러 과목을 신청할 수도 있고, 여러 학생이 한 과목을 신청할 수도 있습니다.
SELECT FOR UPDATE를 쓸 때 잠금 순서(Lock Ordering)가 중요합니다.

제안: 항상 ID 순서대로 잠금을 획득하거나, 수강신청은 한 번에 한 과목만 가능하도록
API를 제한하는 것이 데드락을 피하는 가장 쉬운 방법입니다.
```

**의사결정**: API를 한 번에 한 과목만 신청 가능하도록 설계 → 단일 행 잠금만 발생하므로 데드락 원천 차단.

### 프롬프트 #3: 시드 데이터 멱등성 지시

```
데이터 시딩의 '멱등성(Idempotency)'
서버를 껐다 켤 때마다 데이터가 10,000개씩 늘어나면 곤란합니다.
seed_service.py 시작 부분에 db.query(Student).count()를 체크해서
이미 데이터가 있으면 스킵하는 로직을 꼭 넣으세요.
```

**반영**: `seed_data()` 함수 시작 시 departments 테이블 COUNT 체크, 데이터 존재 시 스킵.

### 프롬프트 #4: Pydantic v2 주의사항

```
FastAPI의 Pydantic v2 (model_config)
FastAPI 최신 버전을 쓰실 텐데, Pydantic v2에서는
orm_mode = True가 from_attributes = True로 바뀌었습니다.
```

**반영**: 모든 스키마에서 `ConfigDict(from_attributes=True)` 사용.

---

## 3. Git 워크플로우 및 커밋 전략

### 프롬프트 #5: 커밋 관리 지시

```
관심사별로 나눠서 커밋해야해.
앞으로 파일수정 있을 시에는 바로바로 커밋하자.
페이스별로 브랜치를 만들어서 피알 날리고 싶은데,
피알은 내가 따로 처리할테니, 페이스별 브랜치 나누기는 지켜줘.
```

**의사결정**:
- 관심사별 커밋 (한꺼번에 몰아서 커밋 금지)
- 파일 수정 즉시 커밋
- Phase별 브랜치 분리 (`feature/phase-4-list-api`, `feature/phase-5-enrollment` 등)
- 커밋 메시지는 영어, 불릿포인트로 상세 설명

### 프롬프트 #6: 커밋 메시지 스타일

```
커밋메세지 세세하게 적어. 필요시 줄바꿈 후 불릿포인트로 설명해.
```

```
커밋메세지는 영어로. (일관성을 위해)
```

**반영**: 커밋 메시지를 conventional commits 형식(영어)으로, 본문에 불릿포인트로 변경 사항 상세 기술.

---

## 4. 문서 우선 작성

### 프롬프트 #7: REQUIREMENTS.md 및 CLAUDE.md 작성 지시

```
요구사항 분석 및 설계 결정을 정리한 REQUIREMENTS.md 를 docs/ 에 생성해줘.
CLAUDE.md 생성한 이후에 개발 속행하자.
```

### 프롬프트 #8: REQUIREMENTS.md 보완 피드백

```
1. 트랜잭션 격리 수준 (Isolation Level) 명시
   SELECT FOR UPDATE를 사용하므로 기본 격리 수준인 Read Committed로도 충분하다는 점을
   명시해주면 DB 이해도가 높다는 것을 어필할 수 있습니다.

2. 실패 시나리오 정의 (99명의 실패자에 대한 응답)
   정원이 꽉 찼을 때 어떤 HTTP 상태 코드를 줄지 명확히 하면 좋습니다.
   보통 리소스 경합 실패는 409를 많이 씁니다.
```

**반영**:
- Read Committed + SELECT FOR UPDATE 조합의 근거 문서화
- 정원 초과, 학점 초과, 시간 충돌 → 409 Conflict로 통일

### 프롬프트 #9: CLAUDE.md에 응답 포맷 포함 지시

```
응답 포맷 통일위한거도 포함해줘
```

**반영**: CLAUDE.md에 `PaginatedResponse`, `SingleResponse`, `ErrorResponse` 형식 명시.

---

## 5. Git 히스토리 재구성

### 프롬프트 #10: 커밋 순서 재배치 요청

```
혹시 이 커밋을 b0c7845 바로 위로 넣을 수 있을까?
지금 관심사별로 브랜치를 나눠서 피알을 하고 main에 머지하고 이런 식으로 해야해서.
CLAUDE.md를 생성하고, REQUIREMENTS.md 커밋 바로 다음에 커밋한 뒤
관심사별로 브랜치 나눠서 피알작업부터 시작하자.
```

**Claude의 행동**: cherry-pick 방식으로 git 히스토리를 재구성.
- `.gitignore` → `REQUIREMENTS.md` → `CLAUDE.md` → 나머지 커밋 순서로 재배치
- 문서가 프로젝트 초기에 위치하도록 히스토리 정리

---

## 6. 개발 진행 중 실시간 피드백

### 프롬프트 #11: 실시간 테스트 요청

```
FastAPI 실행해서 테스트 하면서 진행하고싶어.
```

**반영**: Docker Compose로 PostgreSQL 실행 + uvicorn 서버 백그라운드 실행. curl로 각 API 즉시 검증하며 개발 진행.

### 프롬프트 #12: Bruno 컬렉션 관리 지시

```
브루노 테스트도 라우터 만들거나 API 테스트 할 때 업데이트 해야하는게 있으면
그때그때 업데이트 해줘. 지금 라우터가 도메인 별로 나눠져있는데,
브루노 폴더구조도 그렇게 해줘.
```

**반영**: `.bruno/` 하위에 `auth/`, `students/`, `courses/`, `professors/`, `enrollments/` 도메인별 폴더 구성. 로그인 시 토큰 자동 캡처(`script:post-response`)하여 인증 API에서 `{{ACCESS}}` 변수 사용.

---

## 7. 발생한 기술적 이슈 및 해결

### 이슈 #1: passlib + bcrypt 호환성 문제

- **증상**: Python 3.13 + bcrypt 5.0 환경에서 passlib이 `ValueError: password cannot be longer than 72 bytes` 에러 발생
- **원인**: passlib이 bcrypt 최신 버전과 호환되지 않음
- **해결**: passlib 제거, bcrypt 라이브러리 직접 사용 (`bcrypt.hashpw`, `bcrypt.checkpw`)

### 이슈 #2: Rebase 중 파일 누락

- **증상**: cherry-pick 히스토리 재구성 시 `requirements.txt`, `docker-compose.yml` 누락
- **원인**: 해당 파일들이 커밋되지 않은 상태에서 rebase 진행
- **해결**: Phase 4 브랜치에서 재생성 및 커밋

---

## 주요 의사결정 요약

| # | 결정 사항 | 선택 | 근거 |
|---|----------|------|------|
| 1 | DB | PostgreSQL | SELECT FOR UPDATE 행 잠금으로 동시성 보장 |
| 2 | 인증 | JWT | 프론트 연동 표준, Stateless |
| 3 | 데드락 방지 | 단일 과목 API | 한 번에 한 행만 잠금 → 순환 대기 불가 |
| 4 | 격리 수준 | Read Committed | FOR UPDATE와 조합 시 충분, Serializable 불필요 |
| 5 | 에러 코드 | 409 Conflict | 리소스 경합 실패에 적합 |
| 6 | 시드 멱등성 | COUNT 체크 후 스킵 | 서버 재시작 시 중복 생성 방지 |
| 7 | 커밋 전략 | 관심사별 즉시 커밋 | Git 이력 가독성, Phase별 브랜치 |
| 8 | 응답 포맷 | 통일된 { success, data, meta } | 프론트엔드 일관된 파싱 |
ㅐ
---

## 8. Phase 5: 수강신청/취소 핵심 로직 구현

### 프롬프트 #13: 실시간 테스트와 Bruno 업데이트 지시

```
FastAPI 실행해서 테스트 하면서 진행하고싶어.
브루노 테스트도 라우터 만들거나 API 테스트 할 때 업데이트 해야하는게 있으면 그때그때 업데이트 해줘.
```

**구현 사항**:
- `enrollment_service.py`: `SELECT FOR UPDATE`로 course 행 잠금, 비즈니스 규칙 검증
- 정원/학점/시간충돌/중복 체크 후 409 Conflict 반환
- `enrollments.py` 라우터: POST/DELETE/GET 엔드포인트, JWT 인증 필수
- Bruno 컬렉션: `.bruno/enrollments/` 폴더에 create/cancel/schedule 요청 추가

**실시간 테스트 결과**:
- ✅ 수강신청: 201 Created, enrollment ID와 강좌 정보 반환
- ✅ 중복 신청: 409 Conflict "이미 수강 신청한 강좌입니다."
- ✅ 시간표 조회: 요일 순으로 정렬된 개인 시간표 반환
- ✅ 수강취소: 204 No Content

### 프롬프트 #14: Transcript 문서화 및 지속 업데이트 요청

```
처음부터 지금까지 내가 너랑 대화한거 정리해서
prompts/claude_code_transcript.md 파일로 만들어줘.
평가자가 볼 수 있도록 가독성 좋게 정리해줘.
진행하자. 나랑 대화가 오갈때마다 prompts/claude_code_transcript.md 업데이트 해주면좋겠어.
```

**반영**: 모든 프롬프트와 의사결정을 시간순으로 정리한 Transcript 문서 생성. 이후 대화마다 실시간 업데이트.

---

## 진행 상황 (2026-02-08 현재)

### 완료된 Phase

- ✅ **Phase 1**: 프로젝트 초기화 (Docker, requirements, health endpoint)
- ✅ **Phase 2**: 모델 + 데이터 시드 (10,000명 학생, 500개 강좌, 멱등성 보장)
- ✅ **Phase 3**: JWT 인증 (로그인, 토큰 발급)
- ✅ **Phase 4**: 조회 API (학생/강좌/교수 목록·상세, 페이지네이션)
- ✅ **Phase 5**: 수강신청/취소 (SELECT FOR UPDATE 동시성 제어)

### 남은 Phase

- ⏳ **Phase 6**: 테스트 (pytest, 동시성 테스트 100 concurrent requests)
- ⏳ **Phase 7**: 문서 + Bruno (API.md, README.md 완성)
