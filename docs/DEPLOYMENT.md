# 🚀 Railway 무료 배포 가이드

## 1. Railway 프로젝트 생성

1. [railway.app](https://railway.app) 접속 → GitHub 로그인
2. **New Project** → **Deploy from GitHub repo**
3. 저장소 선택 → `stock-news-bot`
4. **Deploy** 클릭

## 2. PostgreSQL 플러그인 추가

1. 프로젝트 대시보드 → **+ New** → **Database** → **PostgreSQL**
2. 자동 생성된 `DATABASE_URL`은 Railway가 주입합니다

## 3. Redis 플러그인 추가 (선택)

1. **+ New** → **Database** → **Redis**
2. `REDIS_URL`이 자동 주입됩니다

## 4. 환경변수 설정

프로젝트 → **Variables** 탭에서 추가:

```env
# 필수
DATABASE_URL=${{Postgres.DATABASE_URL}}

# 선택 (사용할 채널만)
TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_CHAT_ID=your_chat_id
DISCORD_WEBHOOK_URL=your_webhook_url

# 앱 설정
APP_ENV=production
DEBUG=false
LOG_LEVEL=INFO
CORS_ORIGINS=https://your-frontend.railway.app
```

## 5. 도메인 연결

1. **Settings** → **Networking** → **Generate Domain**
2. `xxx.railway.app` 서브도메인이 자동 생성됩니다
3. 커스텀 도메인도 연결 가능

## 6. 슬립 방지 (cron-job.org)

Railway 무료 티어는 비활성 시 슬립됩니다.

1. [cron-job.org](https://cron-job.org) 가입
2. **New Cron Job** 생성
3. URL: `https://your-app.railway.app/health`
4. 간격: **5분**
5. 활성화

## 7. 로그 확인 + 롤백

- **로그**: 프로젝트 → **Deployments** → 배포 선택 → **View Logs**
- **롤백**: 이전 배포 선택 → **Rollback** 클릭

## 8. 비용 모니터링

- Railway 무료 티어: **월 $5 크레딧**
- **Usage** 탭에서 실시간 확인
- 알림 설정: Settings → Usage → Alert threshold

### 예상 사용량

| 서비스 | 예상 비용/월 |
|--------|-------------|
| App (512MB RAM) | ~$2.5 |
| PostgreSQL | ~$1.0 |
| Redis | ~$0.5 |
| **합계** | **~$4.0** ✅ |
