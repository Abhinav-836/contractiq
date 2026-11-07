"""
Test setup: a throwaway SQLite database per test session, built through the
real migrations (not create_all), and the mock LLM so nothing calls out.
Set before any app module is imported, because settings are read at import.
"""
import os
import sys
import tempfile
from pathlib import Path

_tmp = tempfile.mkdtemp(prefix="contractiq-tests-")
# Default: a fresh SQLite file. Set TEST_DATABASE_URL to an EMPTY Postgres database
# to run the same tests against Postgres.
os.environ["DATABASE_URL"] = os.environ.get("TEST_DATABASE_URL") or f"sqlite+aiosqlite:///{_tmp}/test.db"
os.environ["LLM_PROVIDER"] = "mock"
os.environ["APP_ENV"] = "development"
os.environ["SEED_DEV_USER"] = "false"
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx  # noqa: E402
import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402

from apps.api.main import app  # noqa: E402
from db.session import AsyncSessionLocal, engine, init_db  # noqa: E402


@pytest_asyncio.fixture(scope="session", loop_scope="session", autouse=True)
async def database():
    await init_db()
    yield
    await engine.dispose()


@pytest_asyncio.fixture(loop_scope="session")
async def client():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest_asyncio.fixture(loop_scope="session")
async def db():
    async with AsyncSessionLocal() as session:
        yield session


_counter = {"n": 0}


class User:
    """A registered user with helpers that send their token (and optional workspace)."""

    def __init__(self, client: httpx.AsyncClient, user_id: str, token: str, name: str):
        self.client, self.id, self.token, self.name = client, user_id, token, name

    def headers(self, workspace_id: str | None = None) -> dict:
        h = {"Authorization": f"Bearer {self.token}"}
        if workspace_id:
            h["X-Workspace-Id"] = workspace_id
        return h

    async def get(self, url, ws=None, **kw):
        return await self.client.get(url, headers=self.headers(ws), **kw)

    async def post(self, url, ws=None, **kw):
        return await self.client.post(url, headers=self.headers(ws), **kw)

    async def patch(self, url, ws=None, **kw):
        return await self.client.patch(url, headers=self.headers(ws), **kw)

    async def delete(self, url, ws=None, **kw):
        return await self.client.delete(url, headers=self.headers(ws), **kw)

    async def personal_workspace_id(self) -> str:
        r = await self.get("/api/v1/workspaces")
        return next(w["id"] for w in r.json() if w["is_personal"])


@pytest.fixture
def make_user(client):
    async def _make(name: str = "User") -> User:
        _counter["n"] += 1
        email = f"{name.lower()}{_counter['n']}@example.com"
        r = await client.post(
            "/api/v1/auth/register", json={"email": email, "name": name, "password": "password123"}
        )
        assert r.status_code == 201, r.text
        body = r.json()
        return User(client, body["user"]["id"], body["access_token"], name)

    return _make
