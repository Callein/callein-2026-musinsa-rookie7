# API 문서 (API Documentation)

## 인증 (Authentication)

### 로그인 (Login)
- **URL**: `/api/auth/login`
- **Method**: `POST`
- **설명**: JWT 액세스 토큰을 발급받습니다.
- **요청 본문 (Request Body)**:
  ```json
  {
    "student_number": "학번 (예: 20240001)",
    "password": "비밀번호"
  }
  ```
- **응답 (Response)**:
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR...",
    "token_type": "bearer"
  }
  ```

---

## 학생 (Students)

### 학생 목록 조회 (List Students)
- **URL**: `/api/students`
- **Method**: `GET`
- **쿼리 파라미터**:
  - `page`: 페이지 번호 (기본값: 1)
  - `limit`: 페이지 당 항목 수 (기본값: 20)
  - `department_id`: 학과 ID (선택)
- **응답**:
  ```json
  {
    "success": true,
    "data": [
      {
        "id": 1,
        "name": "홍길동",
        "student_number": "20240001",
        "year": 1,
        "department_id": 1,
        "department_name": "컴퓨터공학과"
      }
    ],
    "meta": {
      "total": 100,
      "page": 1,
      "limit": 20,
      "total_pages": 5
    }
  }
  ```

### 학생 상세 조회 (Get Student Detail)
- **URL**: `/api/students/{id}`
- **Method**: `GET`
- **응답**: 학생 상세 정보

---

## 교수 (Professors)

### 교수 목록 조회 (List Professors)
- **URL**: `/api/professors`
- **Method**: `GET`
- **쿼리 파라미터**: `page`, `limit`, `department_id`
- **응답**:
  ```json
  {
    "success": true,
    "data": [
      {
        "id": 1,
        "name": "김교수",
        "employee_number": "P0001",
        "department_id": 1,
        "department_name": "컴퓨터공학과"
      }
    ],
    "meta": { ... }
  }
  ```

---

## 강좌 (Courses)

### 강좌 목록 조회 (List Courses)
- **URL**: `/api/courses`
- **Method**: `GET`
- **쿼리 파라미터**: `page`, `limit`, `department_id`
- **응답**:
  ```json
  {
    "success": true,
    "data": [
      {
        "id": 1,
        "name": "자료구조",
        "course_code": "CS101",
        "credits": 3,
        "capacity": 30,
        "enrolled": 15,
        "department_id": 1,
        "department_name": "컴퓨터공학과",
        "professor_name": "김교수",
        "schedule": [
          {
            "day_of_week": "월",
            "start_time": "09:00",
            "end_time": "10:15"
          }
        ]
      }
    ],
    "meta": { ... }
  }
  ```

---

## 수강신청 (Enrollment)

### 수강신청 하기 (Enroll in Course)
- **URL**: `/api/enrollments`
- **Method**: `POST`
- **헤더**: `Authorization: Bearer <token>`
- **요청 본문**:
  ```json
  {
    "course_id": 1
  }
  ```
- **응답** (201 Created):
  ```json
  {
    "success": true,
    "data": {
      "id": 1,
      "student_id": 1,
      "course_id": 1,
      "course_name": "자료구조",
      "credits": 3,
      "enrolled_at": "2024-03-01T09:00:00"
    }
  }
  ```
- **에러 (409 Conflict)**:
  - "이미 수강 신청한 강좌입니다."
  - "수강 인원이 마감되었습니다."
  - "시간표가 겹칩니다."
  - "최대 학점을 초과했습니다."

### 수강신청 취소 (Cancel Enrollment)
- **URL**: `/api/enrollments/{enrollment_id}`
- **Method**: `DELETE`
- **헤더**: `Authorization: Bearer <token>`
- **응답**: `204 No Content`

### 내 시간표 조회 (Get My Schedule)
- **URL**: `/api/enrollments/me/schedule`
- **Method**: `GET`
- **헤더**: `Authorization: Bearer <token>`
- **응답**:
  ```json
  {
    "success": true,
    "data": [
      {
        "course_id": 1,
        "course_name": "자료구조",
        "course_code": "CS101",
        "credits": 3,
        "professor_name": "김교수",
        "day_of_week": "월",
        "start_time": "09:00",
        "end_time": "10:15"
      }
    ]
  }
  ```

---

## 상태 확인 (Health Check)
- **URL**: `/health`
- **Method**: `GET`
- **응답**: `{"status": "ok"}`
