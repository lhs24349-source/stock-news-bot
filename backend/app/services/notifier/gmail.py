"""
Gmail SMTP 알림 채널.

aiosmtplib + Jinja2 HTML 템플릿으로 비동기 메일을 전송합니다.
2FA 앱 비밀번호 사용이 필요합니다.
"""

from __future__ import annotations

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.logging import get_logger
from app.services.notifier.base import BaseNotifier, NotificationMessage

logger = get_logger(__name__)

# 간결한 HTML 이메일 템플릿
_HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family:'Apple SD Gothic Neo',sans-serif;max-width:600px;margin:0 auto;padding:20px;background:#f5f5f5;">
  <div style="background:#fff;border-radius:12px;padding:24px;box-shadow:0 2px 8px rgba(0,0,0,0.1);">
    <h2 style="color:#1a1a2e;margin-top:0;">📢 [{group}] 뉴스 알림</h2>
    <p style="color:#666;font-size:14px;">수집 기간: {time_range}</p>
    <hr style="border:none;border-top:1px solid #eee;">
    {articles_html}
    <hr style="border:none;border-top:1px solid #eee;">
    <p style="color:#999;font-size:12px;text-align:center;">
      📊 총 {total_count}건{next_alert}
    </p>
  </div>
</body>
</html>
"""

_ARTICLE_TEMPLATE = """
<div style="padding:8px 0;border-bottom:1px solid #f0f0f0;">
  <strong style="color:#333;">{title}</strong>
  <span style="color:#999;font-size:12px;margin-left:8px;">{time}</span>
  <br>
  <a href="{url}" style="color:#5865F2;font-size:13px;text-decoration:none;">🔗 기사 보기</a>
</div>
"""


class GmailNotifier(BaseNotifier):
    """Gmail SMTP 알림 채널."""

    def __init__(
        self,
        address: str,
        app_password: str,
        recipients: list[str],
    ) -> None:
        self._address = address
        self._app_password = app_password
        self._recipients = recipients

    @property
    def channel_type(self) -> str:
        return "gmail"

    async def send(self, message: NotificationMessage) -> bool:
        """Gmail로 HTML 뉴스 알림을 전송합니다."""
        try:
            articles_html = ""
            for article in message.articles:
                articles_html += _ARTICLE_TEMPLATE.format(
                    title=article.get("title", ""),
                    time=article.get("time", ""),
                    url=article.get("url", "#"),
                )

            next_alert = ""
            if message.next_alert_time:
                next_alert = f" | 다음 알림: {message.next_alert_time}"

            html = _HTML_TEMPLATE.format(
                group=message.keyword_group,
                time_range=message.time_range,
                articles_html=articles_html,
                total_count=message.total_count or len(message.articles),
                next_alert=next_alert,
            )

            subject = (
                f"[Stock News] {message.keyword_group} - "
                f"{len(message.articles)}건의 새 뉴스"
            )

            await self._send_email(subject, html)
            logger.info(
                "Gmail 알림 전송 성공",
                group=message.keyword_group,
                recipients=len(self._recipients),
            )
            return True

        except Exception as e:
            logger.error("Gmail 알림 전송 실패", error=str(e))
            return False

    async def send_test(self, test_message: str) -> bool:
        """테스트 이메일을 전송합니다."""
        try:
            html = f"""
            <html><body style="font-family:sans-serif;padding:20px;">
            <h2>🔔 Stock News Bot 테스트</h2>
            <p>{test_message}</p>
            </body></html>
            """
            await self._send_email("[Stock News] 테스트 알림", html)
            return True
        except Exception as e:
            logger.error("Gmail 테스트 전송 실패", error=str(e))
            return False

    async def health_check(self) -> dict:
        """Gmail SMTP 연결을 확인합니다."""
        try:
            import aiosmtplib

            smtp = aiosmtplib.SMTP(
                hostname="smtp.gmail.com", port=587, use_tls=False
            )
            await smtp.connect()
            await smtp.starttls()
            await smtp.login(self._address, self._app_password)
            await smtp.quit()
            return {"status": "ok", "detail": f"SMTP: {self._address}"}
        except Exception as e:
            return {"status": "error", "detail": str(e)}

    async def _send_email(self, subject: str, html_body: str) -> None:
        """aiosmtplib로 HTML 이메일을 비동기 전송합니다."""
        import aiosmtplib

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self._address
        msg["To"] = ", ".join(self._recipients)
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        await aiosmtplib.send(
            msg,
            hostname="smtp.gmail.com",
            port=587,
            username=self._address,
            password=self._app_password,
            start_tls=True,
        )
