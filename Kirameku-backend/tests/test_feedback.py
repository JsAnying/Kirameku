import unittest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine, select
from app.main import app
from app.database import get_session
from app.models import User
from app.models.feedback import Feedback
from app.api.feedback import _attempts
from app.utils.auth import create_token


class FeedbackTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        SQLModel.metadata.create_all(self.engine)
        with Session(self.engine) as session:
            session.add(User(username="admin", hashed_password="unused", is_admin=True))
            session.commit()
        def override():
            with Session(self.engine) as session:
                yield session
        app.dependency_overrides[get_session] = override
        _attempts.clear()
        self.client = TestClient(app)
        self.admin = {"Authorization": "Bearer " + create_token({"sub": "admin", "admin": True})}

    def tearDown(self):
        self.client.close()
        app.dependency_overrides.clear()
        _attempts.clear()
        self.engine.dispose()

    def submit(self):
        return self.client.post("/api/feedback", json={"type": "suggestion", "content": "希望增加更多文章分类", "contact": "test@example.com"})

    def test_anonymous_submit_private_management(self):
        result = self.submit()
        self.assertEqual(result.status_code, 201)
        self.assertNotIn("contact", result.json())
        for method, path in (("get", "/api/feedback/admin"), ("get", "/api/feedback/admin/1"), ("patch", "/api/feedback/admin/1"), ("delete", "/api/feedback/admin/1")):
            self.assertIn(getattr(self.client, method)(path).status_code, (401, 403))
        reader = {"Authorization": "Bearer " + create_token({"sub": "admin", "type": "github"})}
        self.assertEqual(self.client.get("/api/feedback/admin", headers=reader).status_code, 403)

    def test_admin_workflow_and_filters(self):
        self.submit()
        result = self.client.get("/api/feedback/admin?status=pending&type=suggestion", headers=self.admin).json()
        self.assertEqual(result["total"], 1)
        id = result["items"][0]["id"]
        updated = self.client.patch(f"/api/feedback/admin/{id}", headers=self.admin, json={"status": "resolved", "admin_note": "已记录并安排"})
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(self.client.get(f"/api/feedback/admin/{id}", headers=self.admin).json()["admin_note"], "已记录并安排")
        self.assertEqual(self.client.get("/api/feedback/admin?status=pending", headers=self.admin).json()["total"], 0)
        self.assertEqual(self.client.delete(f"/api/feedback/admin/{id}", headers=self.admin).status_code, 200)
        self.assertEqual(self.client.get(f"/api/feedback/admin/{id}", headers=self.admin).status_code, 404)

    def test_invalid_content_and_client_managed_fields_rejected(self):
        for data in ({"content": "     "}, {"content": "x" * 2001}, {"content": "这是合法的反馈", "status": "resolved"}, {"content": "这是合法的反馈", "page_path": "/posts"}, {"content": "这是合法的反馈", "contact": "a" * 201}):
            _attempts.clear()
            self.assertEqual(self.client.post("/api/feedback", json=data).status_code, 422)
        with Session(self.engine) as session:
            self.assertEqual(list(session.exec(select(Feedback)).all()), [])

    def test_limit_three_submissions_per_minute(self):
        for _ in range(3):
            self.assertEqual(self.submit().status_code, 201)
        result = self.submit()
        self.assertEqual(result.status_code, 429)
        self.assertIn("retry-after", result.headers)

    def test_pagination_and_validation(self):
        with Session(self.engine) as session:
            for i in range(5):
                session.add(Feedback(type="bug", content=f"测试反馈内容{i}"))
            session.commit()
        result = self.client.get("/api/feedback/admin?page=2&size=2", headers=self.admin).json()
        self.assertEqual(result["total"], 5)
        self.assertEqual(len(result["items"]), 2)
        self.assertEqual(self.client.get("/api/feedback/admin?status=invalid", headers=self.admin).status_code, 422)
        self.assertEqual(self.client.patch("/api/feedback/admin/1", headers=self.admin, json={"status": "invalid"}).status_code, 422)


if __name__ == "__main__":
    unittest.main()
