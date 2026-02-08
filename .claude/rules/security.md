# Security Guidelines

## 필수 보안 체크리스트

커밋 전 확인:
- [ ] 하드코딩된 시크릿 없음 (API 키, 비밀번호, 토큰)
- [ ] 모든 사용자 입력 검증됨
- [ ] 에러 메시지에 민감 정보 노출 없음

## 시크릿 관리

```python
import os

# NEVER: 하드코딩
api_key = "sk-proj-xxxxx"

# ALWAYS: 환경 변수
api_key = os.environ.get("API_KEY")
if not api_key:
    raise ValueError("API_KEY 환경변수가 설정되지 않았습니다")
```

## 입력 검증

```python
def validate_price_range(min_price: float, max_price: float) -> None:
    if min_price < 0:
        raise ValueError("가격은 0 이상이어야 합니다")
    if max_price < min_price:
        raise ValueError("최대 가격은 최소 가격보다 커야 합니다")
```
