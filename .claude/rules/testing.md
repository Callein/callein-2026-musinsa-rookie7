# Testing Requirements

## 목표 커버리지: 80%+

## Python (pytest)

### TDD 워크플로우

1. 테스트 먼저 작성 (RED)
2. 테스트 실행 → 실패 확인
3. 최소한의 구현 (GREEN)
4. 테스트 실행 → 통과 확인
5. 리팩토링 (IMPROVE)

### 테스트 구조

```python
# tests/test_product_service.py
import pytest
from src.product_service import ProductService

class TestProductService:
    @pytest.fixture
    def service(self):
        return ProductService()
    
    def test_get_products_returns_list(self, service):
        result = service.get_products()
        assert isinstance(result, list)
    
    def test_filter_by_price_range(self, service):
        result = service.filter_by_price(min=1000, max=5000)
        assert all(1000 <= p["price"] <= 5000 for p in result)
    
    def test_invalid_price_range_raises_error(self, service):
        with pytest.raises(ValueError):
            service.filter_by_price(min=5000, max=1000)
```

### 실행 명령어

```bash
pytest                          # 전체 테스트
pytest -v                       # 상세 출력
pytest --cov=src               # 커버리지 확인
pytest -k "test_filter"        # 특정 테스트만
```

---

## JavaScript (Jest - 참고)

```typescript
describe('ProductService', () => {
  it('should filter products by price', () => {
    const result = filterByPrice(products, 1000, 5000)
    expect(result.every(p => p.price >= 1000 && p.price <= 5000)).toBe(true)
  })
})
```

---

## Agent 활용

- **tdd-guide** → 새 기능 구현 시 TDD 가이드
