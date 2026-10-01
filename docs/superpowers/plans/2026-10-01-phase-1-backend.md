# Phase 1 Backend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** FastAPI에서 고객 문의를 등록·조회하고 PostgreSQL에 영속 저장한다.

**Architecture:** FastAPI는 HTTP 입력과 응답을 검증하고, SQLAlchemy 서비스가 PostgreSQL 트랜잭션에서 고객과 문의를 다룬다. 이 단계에는 LLM과 n8n을 연결하지 않으며, 이후 단계가 사용할 문의 ID와 상태를 확정한다.

**Tech Stack:** Python, FastAPI, Pydantic, SQLAlchemy, Alembic, psycopg, PostgreSQL, pytest, httpx(TestClient), Docker Compose(개발 DB만)

**Spec:** `docs/superpowers/specs/2026-10-01-customer-inquiry-automation-design.md`

## Global Constraints

- Phase 1 범위는 FastAPI, PostgreSQL, 문의 등록·조회와 DB 저장이다.
- 문의 상태는 `RECEIVED`로 시작하며, 이 단계에서는 다른 상태로 전이하지 않는다.
- 데모 데이터는 가상 고객만 사용한다. 실제 개인정보는 저장소에 넣지 않는다.
- API와 DB 코드는 이후 LLM·n8n 단계에서 재사용할 수 있도록 분리한다.
- 개발 DB URL은 `DATABASE_URL`, 별도 테스트 DB URL은 `TEST_DATABASE_URL`에서 읽는다. 테스트는 두 값이 같으면 실행을 중단한다.
- 한 작업을 구현한 뒤 사용자가 직접 실행·확인할 수 있는 명령과 예상 결과를 제공한다. 확인 전 다음 작업으로 넘어가지 않는다.

## Review Focus

- 빈 문의 본문: `POST /inquiries`가 422를 반환하고 DB에 쓰지 않는다. Task 3에서 검증한다.
- 존재하지 않는 고객 ID: `POST /inquiries`가 404를 반환하고 문의를 만들지 않는다. Task 3에서 검증한다.
- 같은 중복 방지 키의 반복 요청: 두 번째 요청은 기존 문의 ID를 반환하고 행을 추가하지 않는다. Task 3에서 검증한다.
- 존재하지 않는 문의 ID: `GET /inquiries/{id}`가 404를 반환한다. Task 4에서 검증한다.
- DB 연결 실패: 서버 시작 또는 DB 사용 시 오류가 숨겨진 성공 응답으로 바뀌지 않는다. Task 2에서 검증한다.

## File Map

| 파일 | 책임 |
|---|---|
| `pyproject.toml` | Python 의존성과 pytest 설정 |
| `app/main.py` | FastAPI 앱과 라우터 등록 |
| `app/api/health.py` | 최소 실행 확인 endpoint |
| `app/api/inquiries.py` | 문의 등록·조회 HTTP 처리 |
| `app/inquiries/schemas.py` | 문의 요청·응답 모델 |
| `app/inquiries/models.py` | 고객·문의 DB 모델 |
| `app/inquiries/service.py` | 고객 확인, 중복 방지, 문의 저장·조회 |
| `app/db.py` | DB URL, engine, 세션 제공 |
| `alembic/` | PostgreSQL 스키마 변경 이력 |
| `scripts/seed_demo.py` | 가상 고객 1명 등록 |
| `compose.yaml` | Phase 1 개발용 PostgreSQL |
| `.env.example` | 개발 환경 변수 예시 |
| `tests/conftest.py` | 테스트 DB 연결과 테스트 데이터 격리 |
| `tests/` | API와 DB 동작 검증 |

## Task 1: FastAPI 최소 실행

**Files:** `pyproject.toml`, `app/main.py`, `app/api/health.py`, `tests/test_health.py`

**Interfaces:** `app.main:app`; `GET /health -> {"status": "ok"}`.

- [ ] 실패하는 `test_health_returns_ok`를 작성한다. `TestClient`로 `/health`의 200과 응답 본문을 확인한다.
- [ ] `python -m pytest tests/test_health.py -q`로 실패를 확인한다.
- [ ] `app.main:app`과 `/health`를 최소 구현한다.
- [ ] 같은 테스트가 통과하는지 확인한다.
- [ ] `python -m uvicorn app.main:app --reload` 실행 방법과 `/health` 직접 확인 방법을 사용자에게 안내한다.
- [ ] 사용자가 직접 확인한 뒤 변경 파일을 커밋한다.

## Task 2: PostgreSQL 연결과 스키마

**Files:** `app/db.py`, `app/inquiries/models.py`, `alembic/`, `scripts/seed_demo.py`, `compose.yaml`, `.env.example`, `tests/test_database.py`

**Interfaces:** `get_session()`은 요청 범위 SQLAlchemy `Session`을 제공한다. `Customer(id: UUID, display_name: str)`와 `Inquiry(id: UUID, customer_id: UUID, body: str, status: str, idempotency_key: str, created_at: datetime)` 모델을 만든다. `inquiries.idempotency_key`는 고유하며 `created_at`은 UTC 시각이다.

- [ ] PostgreSQL 테스트 DB에서 마이그레이션 후 고객과 문의를 저장·재조회하는 실패 테스트를 작성한다. DB 연결 실패도 성공으로 처리되지 않는지 확인한다.
- [ ] 테스트 실패를 확인한다.
- [ ] 개발용 PostgreSQL 설정, DB 세션, 고객·문의 모델, 첫 Alembic 마이그레이션, 가상 고객 seed 명령을 구현한다.
- [ ] 테스트가 통과하는지 확인한다.
- [ ] DB 시작, 마이그레이션, seed 실행과 저장 결과 확인 방법을 사용자에게 안내한다.
- [ ] 사용자가 직접 확인한 뒤 변경 파일을 커밋한다.

## Task 3: 문의 등록 API

**Files:** `app/api/inquiries.py`, `app/inquiries/schemas.py`, `app/inquiries/service.py`, `app/main.py`, `tests/test_create_inquiry.py`

**Interfaces:** `POST /inquiries`는 `customer_id`, 공백만으로 이뤄지지 않은 `body`, `idempotency_key`를 받는다. 최초 등록은 201과 `id`, `status=RECEIVED`를 반환한다. 같은 키의 동일 요청은 기존 ID를 200으로 반환한다. 같은 키에 다른 내용이 오면 409를 반환한다.

- [ ] 정상 등록, 빈 본문 422, 없는 고객 404, 동일 요청 반복 200·동일 ID, 같은 키와 다른 본문 409를 검증하는 실패 테스트를 작성한다.
- [ ] 테스트 실패를 확인한다.
- [ ] 스키마와 등록 서비스를 구현한다. 고유 제약 충돌 시 기존 문의를 재조회해 동일 요청 여부를 판정한다.
- [ ] 테스트가 통과하는지 확인한다.
- [ ] 사용자가 가상 고객으로 문의를 직접 등록하고 반복 요청을 확인하도록 안내한다.
- [ ] 사용자가 직접 확인한 뒤 변경 파일을 커밋한다.

## Task 4: 문의 조회 API와 Phase 1 확인

**Files:** `app/api/inquiries.py`, `app/inquiries/service.py`, `app/inquiries/schemas.py`, `tests/test_get_inquiry.py`, `README.md`

**Interfaces:** `GET /inquiries/{id}`는 `id`, `customer_id`, `body`, `status`, `created_at`을 반환한다. 없는 ID는 404다.

- [ ] 등록한 문의 조회와 없는 ID의 404를 검증하는 실패 테스트를 작성한다.
- [ ] 테스트 실패를 확인한다.
- [ ] 조회 서비스와 응답 모델을 구현한다.
- [ ] Phase 1 전체 테스트를 실행하고 결과를 확인한다.
- [ ] README에 개발 DB 실행, 서버 실행, 문의 등록·조회 예시를 기록한다.
- [ ] 사용자가 서버 재시작 후에도 문의가 조회되는지 직접 확인하도록 안내한다.
- [ ] 사용자가 확인한 뒤 Phase 1 변경 파일을 커밋한다.

## Phase 1 종료 조건

사용자가 `/health`, 문의 등록, 동일 요청 반복, 문의 조회, 서버 재시작 후 조회를 직접 확인한다. 자동 테스트는 PostgreSQL을 사용하는 경로에서 통과해야 한다. 그다음 Phase 2의 LLM 입력·출력 계약을 설계한다.
