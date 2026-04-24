# 🔧 트러블슈팅 가이드

## 1. 네이버 RSS 한글 깨짐

**증상**: 네이버 RSS 뉴스 제목이 깨진 문자로 표시됨

**원인**: 네이버 RSS가 EUC-KR 인코딩으로 응답

**해결**: 앱이 `chardet`로 자동 감지합니다. 수동 확인:
```python
import chardet
result = chardet.detect(response.content)
print(result)  # {'encoding': 'EUC-KR', 'confidence': 0.99}
```

## 2. Telegram 봇 토큰 오류

**증상**: `Unauthorized: bot token is invalid`

**해결**:
1. @BotFather에서 `/token` 명령으로 토큰 재확인
2. `.env`에 공백 없이 입력: `TELEGRAM_BOT_TOKEN=123456:ABC...`
3. Chat ID 확인: `https://api.telegram.org/bot<TOKEN>/getUpdates`

## 3. Gmail 인증 실패

**증상**: `SMTPAuthenticationError: Username and Password not accepted`

**해결**:
1. Google 계정 → 보안 → **2단계 인증** 활성화
2. 보안 → 2단계 인증 → **앱 비밀번호** 생성
3. 생성된 16자리 비밀번호를 `GMAIL_APP_PASSWORD`에 입력
4. 일반 비밀번호가 아닌 **앱 비밀번호**를 사용해야 합니다

## 4. Discord 429 Rate Limit

**증상**: `HTTP 429 Too Many Requests`

**해결**: 앱이 `Retry-After` 헤더를 자동으로 준수합니다. 빈번한 경우:
- 웹훅 호출 간격을 늘리세요 (스케줄 설정)
- Discord는 웹훅당 초당 5회 제한

## 5. feedparser 파싱 실패

**증상**: RSS 피드는 정상이지만 뉴스가 수집되지 않음

**해결**:
1. 로그 확인: `feedparser 파싱 경고` 메시지 검색
2. RSS URL을 브라우저에서 직접 확인
3. User-Agent 차단 가능성 → 앱은 자동으로 브라우저 UA 사용

## 6. SQLite 동시 접근 오류

**증상**: `database is locked`

**해결**: SQLite는 동시 쓰기에 제한이 있습니다.
- 개발/테스트에서만 SQLite 사용
- 운영 환경에서는 PostgreSQL로 전환:
  ```env
  DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname
  ```

## 7. APScheduler 중복 실행

**증상**: 같은 작업이 여러 번 실행됨

**해결**: 앱에서 `coalesce=True`, `max_instances=1`을 설정하고 있습니다.
- Docker 재시작 시 이전 작업이 남아있을 수 있음
- `/api/schedule/jobs` 엔드포인트로 현재 작업 확인

## 8. CORS 오류

**증상**: 프론트엔드에서 API 호출 시 CORS 에러

**해결**:
```env
CORS_ORIGINS=http://localhost:5173,http://localhost:3000,https://your-domain.com
```

## 9. Redis 연결 실패

**증상**: Redis 연결 오류 로그

**해결**: Redis는 선택사항입니다. 미설치 시 자동으로 SQLite 폴백.
```env
# Redis 사용하지 않으려면 이 줄을 주석 처리
# REDIS_URL=redis://localhost:6379/0
```

## 10. Railway 슬립 모드

**증상**: 앱이 일정 시간 후 응답하지 않음

**해결**: [DEPLOYMENT.md](DEPLOYMENT.md)의 6번 섹션 참고
- cron-job.org에서 5분 간격 `/health` ping 설정
