# Git Workflow (GitHub Flow)

## 브랜치 전략

```
main (항상 배포 가능)
  └── feature/add-product-filter
  └── feature/implement-ranking
  └── fix/price-validation
```

### 규칙
- `main`은 항상 안정적인 상태 유지
- 새 작업은 `main`에서 브랜치 생성
- 브랜치명: `feature/기능명`, `fix/버그명`

## 워크플로우

```bash
# 1. main에서 브랜치 생성
git checkout main
git pull origin main
git checkout -b feature/add-product-filter

# 2. 작업 및 커밋
git add .
git commit -m "feat(product): add price filter"

# 3. 푸시 및 PR (시험에서는 직접 main 머지 가능)
git push -u origin feature/add-product-filter
```

## 커밋 메시지 형식

```
<type>: <description>

<optional body>
```

### Types
- `feat`: 새 기능
- `fix`: 버그 수정
- `docs`: 문서 수정
- `style`: 포맷 변경 (코드 의미 변경 없음)
- `refactor`: 코드 개선
- `perf`: 성능 개선
- `test`: 테스트 추가/수정
- `chore`: 설정, 도구

### 예시
```
feat(product): add price range filter
fix(ranking): correct score calculation
test(product): add filter edge cases
```

## Feature Implementation Workflow

1. **Plan First**
   - Use **planner** agent to create implementation plan
   - Identify dependencies and risks
   - Break down into phases

2. **TDD Approach**
   - Use **tdd-guide** agent
   - Write tests first (RED)
   - Implement to pass tests (GREEN)
   - Refactor (IMPROVE)
   - Verify 80%+ coverage

3. **Code Review**
   - Use **code-reviewer** agent immediately after writing code
   - Address CRITICAL and HIGH issues
   - Fix MEDIUM issues when possible

4. **Commit & Push**
   - Detailed commit messages
   - Follow conventional commits format
