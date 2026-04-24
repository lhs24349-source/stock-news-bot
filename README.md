# 📰 Stock News Bot - 주식 뉴스 알림 웹앱

키워드 기반 주식 뉴스 자동 수집 및 다채널 알림 서비스입니다.

## ✨ 주요 기능

- **RSS 뉴스 수집**: 네이버 금융, 구글 뉴스 RSS 실시간 수집
- **키워드 매칭**: rapidfuzz 기반 퍼지 매칭 (유사도 85%+)
- **3-tier 중복 제거**: URL 해시 → 제목 유사도 → 키워드 그룹별 재알림 방지
- **다채널 알림**: Telegram / Discord / Gmail 독립 동작
- **4가지 스케줄**: Backfill / Interval / Digest(Cron) / Event
- **웹 대시보드**: React 기반 관리 UI

## 🚀 빠른 시작 (5분)

### 방법 1: 로컬 실행 (Python만 필요)

```bash
# 1. 클론
git clone <repo> && cd stock-news-bot

# 2. 가상환경 + 의존성
cd backend
python -m venv venv
venv\Scripts\activate    # Windows
pip install -r requirements.txt

# 3. 환경변수 설정
copy .env.example .env
# .env를 열어서 원하는 알림 채널 토큰 입력 (선택사항)

# 4. 서버 실행
uvicorn app.main:app --reload --port 8000

# 5. Swagger UI 확인
# http://localhost:8000/docs
```

### 방법 2: Docker (권장)

```bash
# 1. 환경변수
cp backend/.env.example backend/.env
# .env 편집 (토큰 입력)

# 2. 실행
docker-compose -f infra/docker-compose.yml up -d

# 3. 확인
curl http://localhost:8000/health
```

## 📡 API 사용 예시

### 헬스체크
```bash
curl http://localhost:8000/health
```

### 즉시 백필 (반도체 뉴스 24시간)
```bash
curl -X POST http://localhost:8000/api/news/backfill \
  -H "Content-Type: application/json" \
  -d '{"keywords":["반도체","HBM"],"hours":24}'
```

### 키워드 그룹 생성
```bash
curl -X POST http://localhost:8000/api/keywords \
  -H "Content-Type: application/json" \
  -d '{"name":"반도체","keywords":["HBM","메모리","DRAM"],"exclude_keywords":["광고"]}'
```

## 🔧 환경 변수

| 변수 | 필수 | 설명 |
|------|------|------|
| `DATABASE_URL` | ✅ | DB URL (기본: SQLite) |
| `REDIS_URL` | ❌ | Redis URL (미설정 시 SQLite 폴백) |
| `TELEGRAM_BOT_TOKEN` | ❌ | Telegram 봇 토큰 |
| `TELEGRAM_CHAT_ID` | ❌ | Telegram 채팅 ID |
| `DISCORD_WEBHOOK_URL` | ❌ | Discord 웹훅 URL |
| `GMAIL_ADDRESS` | ❌ | Gmail 주소 |
| `GMAIL_APP_PASSWORD` | ❌ | Gmail 앱 비밀번호 (2FA) |
| `GMAIL_RECIPIENTS` | ❌ | 수신자 (쉼표 구분) |

> 💡 **토큰 1개만 있어도** 해당 채널 단독으로 동작합니다.
> 알림 채널 0개여도 `/api/news` API는 정상 작동합니다.

## 🧪 테스트

```bash
cd backend
pip install -r requirements-dev.txt
pytest --cov=app --cov-report=term-missing -v
```

## 📚 문서

- [배포 가이드](docs/DEPLOYMENT.md) - Railway 무료 배포
- [트러블슈팅](docs/TROUBLESHOOTING.md) - 흔한 오류 해결
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🏗️ 기술 스택

| 영역 | 기술 |
|------|------|
| Backend | FastAPI, SQLAlchemy 2.0, APScheduler |
| Frontend | React 18, TypeScript, TailwindCSS, shadcn/ui |
| Database | SQLite (dev) / PostgreSQL (prod) |
| Cache | Redis / SQLite 폴백 |
| 알림 | Telegram, Discord, Gmail |
