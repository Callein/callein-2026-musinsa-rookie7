# Coding Style

## Python (Primary)

### 불변성 (Immutability)

```python
# WRONG: 원본 변경
def update_user(user: dict, name: str) -> dict:
    user["name"] = name  # MUTATION!
    return user

# CORRECT: 새 객체 생성
def update_user(user: dict, name: str) -> dict:
    return {**user, "name": name}
```

### 타입 힌트 (Type Hints)

```python
from typing import Optional, List

def get_products(
    min_price: float,
    max_price: float,
    limit: Optional[int] = None
) -> List[dict]:
    ...
```

### 에러 처리

```python
try:
    result = risky_operation()
    return result
except ValueError as e:
    logger.error(f"Operation failed: {e}")
    raise ValueError("사용자 친화적 메시지") from e
```

---

## JavaScript/TypeScript (참고)

```typescript
// 불변성
const updateUser = (user: User, name: string): User => ({
  ...user,
  name
})

// 입력 검증 (zod)
const schema = z.object({
  email: z.string().email(),
  age: z.number().int().min(0)
})
```

---

## 공통 원칙
- [ ] Code is readable and well-named
- [ ] Functions are small (<50 lines)
- [ ] Files are focused (<800 lines)
- [ ] No deep nesting (>4 levels)
- [ ] Proper error handling
- [ ] No console.log statements
- [ ] No hardcoded values
- [ ] No mutation (immutable patterns used)