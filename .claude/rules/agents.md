# Agent Orchestration

## Available Agents

| Agent | Purpose | When to Use |
|-------|---------|-------------|
| planner | 구현 계획 수립 | 문제 분석, 복잡한 기능 설계 |
| tdd-guide | 테스트 주도 개발 | 기능 구현, 버그 수정 |
| code-reviewer | 코드 리뷰 | 커밋 전 품질 점검 |
| refactor-cleaner | 코드 정리 | 리팩토링, 중복 제거 |
| doc-updater | 문서 업데이트 | README, 주석 정리 |

## Immediate Agent Usage

- 문제 분석 시작 → **planner**
- 기능 구현 → **tdd-guide**
- 커밋 전 검토 → **code-reviewer**
- 마무리 문서화 → **doc-updater**

## Parallel Task Execution

독립적인 작업은 병렬로 실행하여 시간 절약:

```markdown
# GOOD: 병렬 실행
3개 에이전트 동시 실행:
1. Agent 1: 모듈 A 테스트 작성
2. Agent 2: 모듈 B 리팩토링
3. Agent 3: 타입 힌트 추가

# BAD: 불필요한 순차 실행
Agent 1 완료 → Agent 2 시작 → Agent 3 시작
```
