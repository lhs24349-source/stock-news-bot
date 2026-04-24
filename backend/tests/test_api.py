"""
API 엔드포인트 통합 테스트.

FastAPI TestClient로 실제 HTTP 요청/응답을 검증합니다.
"""

from __future__ import annotations

import pytest
import pytest_asyncio


class TestHealthCheck:
    """헬스 체크 API 테스트."""

    @pytest.mark.asyncio
    async def test_health_200(self, client):
        """헬스체크가 200을 반환하는지 확인."""
        resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] in ("ok", "degraded")
        assert "db" in data
        assert "channels" in data


class TestKeywordsAPI:
    """키워드 그룹 CRUD API 테스트."""

    @pytest.mark.asyncio
    async def test_키워드그룹_생성_조회(self, client):
        """키워드 그룹 생성 후 조회가 되는지 확인."""
        # 생성
        resp = await client.post("/api/keywords", json={
            "name": "테스트그룹",
            "keywords": ["HBM", "메모리"],
            "exclude_keywords": ["광고"],
            "threshold": 85.0,
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "테스트그룹"
        group_id = data["id"]

        # 조회
        resp = await client.get("/api/keywords")
        assert resp.status_code == 200
        groups = resp.json()
        assert any(g["id"] == group_id for g in groups)

    @pytest.mark.asyncio
    async def test_키워드그룹_중복이름(self, client):
        """중복 이름 생성이 409를 반환하는지 확인."""
        payload = {
            "name": "중복테스트",
            "keywords": ["테스트"],
        }
        await client.post("/api/keywords", json=payload)
        resp = await client.post("/api/keywords", json=payload)
        assert resp.status_code == 409

    @pytest.mark.asyncio
    async def test_키워드그룹_삭제(self, client):
        """키워드 그룹 삭제가 동작하는지 확인."""
        resp = await client.post("/api/keywords", json={
            "name": "삭제테스트",
            "keywords": ["테스트"],
        })
        group_id = resp.json()["id"]

        resp = await client.delete(f"/api/keywords/{group_id}")
        assert resp.status_code == 204


class TestNewsAPI:
    """뉴스 API 테스트."""

    @pytest.mark.asyncio
    async def test_뉴스_목록_빈결과(self, client):
        """뉴스 목록이 빈 결과를 반환하는지 확인."""
        resp = await client.get("/api/news")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["items"] == []

    @pytest.mark.asyncio
    async def test_뉴스_404(self, client):
        """존재하지 않는 뉴스 ID가 404를 반환하는지 확인."""
        resp = await client.get("/api/news/99999")
        assert resp.status_code == 404


class TestChannelsAPI:
    """알림 채널 API 테스트."""

    @pytest.mark.asyncio
    async def test_채널_CRUD(self, client):
        """채널 생성/조회/삭제 흐름을 확인."""
        # 생성
        resp = await client.post("/api/channels", json={
            "channel_type": "telegram",
            "name": "테스트 텔레그램",
            "config": {"bot_token": "test", "chat_id": "123"},
        })
        assert resp.status_code == 201
        ch_id = resp.json()["id"]

        # 조회
        resp = await client.get("/api/channels")
        assert resp.status_code == 200

        # 삭제
        resp = await client.delete(f"/api/channels/{ch_id}")
        assert resp.status_code == 204
