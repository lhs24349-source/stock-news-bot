# 자주 사용하는 명령어 모음
.PHONY: help dev test lint docker-up docker-down

help: ## 도움말 표시
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ── 개발 ──────────────────────────────────────

dev: ## 백엔드 개발 서버 실행
	cd backend && venv\Scripts\uvicorn.exe app.main:app --reload --host 0.0.0.0 --port 8000

frontend-dev: ## 프론트엔드 개발 서버 실행
	cd frontend && npm run dev

install: ## 백엔드 의존성 설치
	cd backend && venv\Scripts\pip.exe install -r requirements-dev.txt

# ── 테스트 ────────────────────────────────────

test: ## pytest 실행 (커버리지 포함)
	cd backend && venv\Scripts\pytest.exe --cov=app --cov-report=term-missing -v

test-fast: ## pytest 실행 (커버리지 없이)
	cd backend && venv\Scripts\pytest.exe -v -x

# ── 린팅 ──────────────────────────────────────

lint: ## ruff 린팅
	cd backend && venv\Scripts\ruff.exe check app/ tests/

lint-fix: ## ruff 자동 수정
	cd backend && venv\Scripts\ruff.exe check --fix app/ tests/

# ── Docker ────────────────────────────────────

docker-up: ## Docker 개발 환경 시작
	docker-compose -f infra/docker-compose.yml up -d --build

docker-down: ## Docker 환경 종료
	docker-compose -f infra/docker-compose.yml down

docker-logs: ## Docker 로그 확인
	docker-compose -f infra/docker-compose.yml logs -f app

# ── 데이터베이스 ──────────────────────────────

db-migrate: ## Alembic 마이그레이션 생성
	cd backend && venv\Scripts\alembic.exe revision --autogenerate -m "$(msg)"

db-upgrade: ## Alembic 마이그레이션 적용
	cd backend && venv\Scripts\alembic.exe upgrade head
