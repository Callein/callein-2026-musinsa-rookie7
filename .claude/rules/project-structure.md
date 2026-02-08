# Python Project Structure

## 표준 구조

```
project_root/
├── src/                    # 소스 코드
│   ├── __init__.py
│   ├── main.py             # 진입점
│   ├── services/           # 비즈니스 로직
│   │   ├── __init__.py
│   │   └── product_service.py
│   ├── models/             # 데이터 모델
│   │   ├── __init__.py
│   │   └── product.py
│   └── utils/              # 유틸리티
│       ├── __init__.py
│       └── helpers.py
├── tests/                  # 테스트
│   ├── __init__.py
│   ├── test_product_service.py
│   └── conftest.py         # pytest fixtures
├── data/                   # 데이터 파일 (JSON, CSV 등)
│   └── products.json
├── requirements.txt        # 의존성
├── pyproject.toml          # (선택) 프로젝트 메타데이터
├── .gitignore
└── README.md
```

## 파일별 역할

| 파일/폴더 | 역할 |
|----------|------|
| `src/main.py` | 애플리케이션 진입점 |
| `src/services/` | 핵심 비즈니스 로직 |
| `src/models/` | 데이터 클래스, Pydantic 모델 등 |
| `src/utils/` | 공통 헬퍼 함수 |
| `tests/` | pytest 테스트 파일 |
| `tests/conftest.py` | 공용 fixture 정의 |
| `data/` | 입력 데이터 파일 |

## 네이밍 규칙

- **파일명**: snake_case (`product_service.py`)
- **클래스**: PascalCase (`ProductService`)
- **함수/변수**: snake_case (`get_products`)
- **상수**: UPPER_SNAKE_CASE (`MAX_PRICE`)

## 초기 설정 명령어

```bash
# 디렉토리 생성
mkdir -p src/services src/models src/utils tests data

# __init__.py 생성
touch src/__init__.py src/services/__init__.py src/models/__init__.py src/utils/__init__.py tests/__init__.py

# 기본 파일 생성
touch src/main.py requirements.txt README.md .gitignore
```
