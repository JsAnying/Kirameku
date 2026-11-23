import unittest

from fastapi.testclient import TestClient
from jose import jwt
from sqlmodel import SQLModel, Session, create_engine, select
from sqlalchemy.pool import StaticPool

from app.config import SECRET_KEY, ALGORITHM
from app.database import get_session
from app.main import app
from app.models import (
    User, GitHubUser, Post, Comment, Tag, Chatter, ChatterComment, Message,
    Category, PostTag, Album, Photo, BookmarkCategory, BookmarkSite,
)
from app.utils.auth import create_token


class ApiRegressionTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        with self.engine.connect() as connection:
            connection.exec_driver_sql("PRAGMA foreign_keys=ON")
        SQLModel.metadata.create_all(self.engine)
        with Session(self.engine) as session:
            session.add(User(username="admin", hashed_password="unused", is_admin=True))
            session.add(GitHubUser(id=1, github_id=123, login="reader"))
            session.add(Post(id=1, title="Public", slug="public", status="published"))
            session.add(Post(id=2, title="Draft", slug="draft", status="draft"))
            session.add(Post(id=3, title="Other", slug="other", status="published"))
            session.add(Chatter(id=1, content="draft", status="draft"))
            session.add(Chatter(id=2, content="public", status="published", comments_count=1))
            session.add(Chatter(id=3, content="other", status="published"))
            session.flush()
            session.add(Comment(id=1, post_id=1, content="parent", github_user_id=1))
            session.add(ChatterComment(id=1, chatter_id=2, content="parent", github_user_id=1))
            session.commit()
        def session_override():
            with Session(self.engine) as session:
                yield session
        app.dependency_overrides[get_session] = session_override
        self.client = TestClient(app)
        self.admin = {"Authorization": "Bearer " + create_token({"sub": "admin", "admin": True})}
        self.reader = {"Authorization": "Bearer " + jwt.encode({"sub": "1", "type": "github"}, SECRET_KEY, algorithm=ALGORITHM)}

    def tearDown(self):
        self.client.close()
        app.dependency_overrides.clear()
        self.engine.dispose()

    def test_admin_and_reader_tokens_are_not_interchangeable(self):
        self.assertEqual(self.client.get('/api/posts/detail/2', headers=self.reader).status_code, 403)
        self.assertEqual(self.client.get('/api/posts/detail/2', headers=self.admin).status_code, 200)
        self.assertEqual(self.client.get('/api/auth/github/me', headers=self.admin).status_code, 401)
        self.assertEqual(self.client.post('/api/auth/github/callback?code=x').status_code, 405)
        self.assertEqual(self.client.get('/api/auth/github/callback?code=x').status_code, 400)

    def test_public_cannot_read_drafts_or_unmatched_filters(self):
        response = self.client.get('/api/posts?status=draft')
        self.assertEqual({p['slug'] for p in response.json()}, {'public', 'other'})
        self.assertEqual(self.client.get('/api/posts/draft').status_code, 404)
        self.assertEqual(self.client.get('/api/posts?category=missing').json(), [])
        self.assertEqual(self.client.get('/api/posts?tag=missing').json(), [])
        self.assertEqual(len(self.client.get('/api/posts?status=draft', headers=self.admin).json()), 1)

    def test_comment_parent_must_belong_to_published_post(self):
        response = self.client.post('/api/comments', headers=self.reader, json={"post_id": 3, "parent_id": 1, "content": "reply"})
        self.assertEqual(response.status_code, 404)
        response = self.client.post('/api/comments', headers=self.reader, json={"post_id": 2, "content": "draft"})
        self.assertEqual(response.status_code, 404)
        response = self.client.post('/api/comments', headers=self.reader, json={"post_id": 1, "parent_id": 1, "content": "reply"})
        self.assertEqual(response.status_code, 200)

    def test_chatter_drafts_and_cross_chatter_replies(self):
        self.assertEqual(self.client.get('/api/chatters/1').status_code, 404)
        self.assertEqual(self.client.get('/api/chatters/1', headers=self.admin).status_code, 200)
        self.assertEqual(self.client.get('/api/chatters/count?status=draft').json()['count'], 2)
        response = self.client.post('/api/chatters/comments', headers=self.reader, json={"chatter_id": 3, "parent_id": 1, "content": "reply"})
        self.assertEqual(response.status_code, 404)
        response = self.client.post('/api/chatters/comments', headers=self.reader, json={"chatter_id": 1, "content": "draft"})
        self.assertEqual(response.status_code, 404)

    def test_duplicate_tags_and_tag_counts(self):
        response = self.client.post('/api/posts', headers=self.admin, json={"title": "Tagged", "slug": "tagged", "tags": ["one", " one ", "two"]})
        self.assertEqual(response.status_code, 200, response.text)
        post_id = response.json()['id']
        response = self.client.put(f'/api/posts/{post_id}', headers=self.admin, json={"tags": ["one", "one"]})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()['tags'], ['one'])
        self.assertEqual(self.client.delete(f'/api/posts/{post_id}', headers=self.admin).status_code, 200)
        with Session(self.engine) as session:
            self.assertEqual(session.exec(select(Tag).where(Tag.name == 'one')).one().post_count, 0)

    def test_reader_tokens_can_access_public_endpoints(self):
        for path in ('/api/posts', '/api/posts/count', '/api/chatters/count', '/api/chatters/2'):
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path, headers=self.reader).status_code, 200)

    def test_hidden_content_cannot_be_read_or_liked_publicly(self):
        with Session(self.engine) as session:
            session.add(Comment(id=2, post_id=2, content="draft comment"))
            session.add(Comment(id=3, post_id=1, content="rejected comment", status="rejected"))
            session.add(ChatterComment(id=2, chatter_id=1, content="draft comment"))
            session.add(ChatterComment(id=3, chatter_id=2, content="rejected comment", status="rejected"))
            session.add(Message(id=1, content="rejected message", status="rejected"))
            session.commit()
        for path in ('/api/comments/post/2', '/api/comments/post/999', '/api/chatters/1/comments', '/api/chatters/999/comments'):
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 404)
        for path in ('/api/posts/2', '/api/chatters/1', '/api/comments/2', '/api/comments/3', '/api/chatters/comments/2', '/api/chatters/comments/3', '/api/messages/1'):
            for action in ('like', 'unlike'):
                with self.subTest(path=path, action=action):
                    self.assertEqual(self.client.post(f'{path}/{action}').status_code, 404)
        response = self.client.post('/api/messages', headers=self.reader, json={"parent_id": 1, "content": "reply"})
        self.assertEqual(response.status_code, 404)

    def test_chatter_comment_count_tracks_moderation_and_deletion(self):
        response = self.client.post('/api/chatters/comments', headers=self.reader, json={"chatter_id": 2, "parent_id": 1, "content": "reply"})
        self.assertEqual(response.status_code, 200)
        reply_id = response.json()['id']
        self.assertEqual(self.client.get('/api/chatters/2').json()['comments_count'], 2)
        for status, count in (('rejected', 1), ('rejected', 1), ('approved', 2)):
            response = self.client.put(f'/api/chatters/comments/{reply_id}/status', headers=self.admin, json={"status": status})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(self.client.get('/api/chatters/2').json()['comments_count'], count)
        self.assertEqual(self.client.delete(f'/api/chatters/comments/{reply_id}', headers=self.admin).status_code, 200)
        self.assertEqual(self.client.get('/api/chatters/2').json()['comments_count'], 1)
        self.assertEqual(self.client.delete('/api/chatters/comments/1', headers=self.admin).status_code, 200)
        self.assertEqual(self.client.get('/api/chatters/2').json()['comments_count'], 0)

    def test_deleting_parent_comment_removes_replies_and_updates_count(self):
        response = self.client.post('/api/chatters/comments', headers=self.reader, json={"chatter_id": 2, "parent_id": 1, "content": "reply"})
        self.assertEqual(response.status_code, 200)
        response = self.client.delete('/api/chatters/comments/1', headers=self.admin)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.get('/api/chatters/2').json()['comments_count'], 0)
        self.assertEqual(self.client.get('/api/chatters/2/comments').json(), [])

    def test_deleting_posts_and_chatters_removes_comments(self):
        for path in ('/api/posts/1', '/api/chatters/2'):
            with self.subTest(path=path):
                self.assertEqual(self.client.delete(path, headers=self.admin).status_code, 200)
        with Session(self.engine) as session:
            self.assertIsNone(session.get(Comment, 1))
            self.assertIsNone(session.get(ChatterComment, 1))

    def test_deleting_categories_and_tags_preserves_posts(self):
        with Session(self.engine) as session:
            category = Category(id=1, name="category", slug="category")
            tag = Tag(id=1, name="tag", slug="tag")
            session.add_all([category, tag])
            session.flush()
            post = session.get(Post, 1)
            post.category_id = 1
            session.add(post)
            session.add(PostTag(post_id=1, tag_id=1))
            session.commit()
            session.delete(category)
            session.delete(tag)
            session.commit()
            self.assertIsNone(session.get(Post, 1).category_id)
            self.assertEqual(session.exec(select(PostTag)).all(), [])

    def test_deleting_album_and_bookmark_category_removes_children(self):
        with Session(self.engine) as session:
            album = Album(id=1, title="album")
            category = BookmarkCategory(id=1, name="links")
            session.add_all([album, category])
            session.flush()
            session.add(Photo(id=1, album_id=1, url="https://example.com/image.jpg"))
            session.add(BookmarkSite(id=1, category_id=1, name="site", url="https://example.com"))
            session.commit()
            session.delete(album)
            session.delete(category)
            session.commit()
            self.assertIsNone(session.get(Photo, 1))
            self.assertIsNone(session.get(BookmarkSite, 1))

    def test_deleting_reader_preserves_comments_and_deleting_threads_removes_replies(self):
        with Session(self.engine) as session:
            session.add(Message(id=1, github_user_id=1, content="root"))
            session.flush()
            session.add(Message(id=2, parent_id=1, github_user_id=1, content="reply"))
            session.add(Comment(id=2, post_id=1, parent_id=1, github_user_id=1, content="reply"))
            session.commit()
            session.delete(session.get(GitHubUser, 1))
            session.commit()
            for model in (Comment, ChatterComment, Message):
                self.assertIsNone(session.get(model, 1).github_user_id)
        for path in ('/api/comments/1', '/api/messages/1'):
            self.assertEqual(self.client.delete(path, headers=self.admin).status_code, 200)
        with Session(self.engine) as session:
            self.assertIsNone(session.get(Comment, 2))
            self.assertIsNone(session.get(Message, 2))

    def test_public_messages_do_not_disclose_ip_addresses(self):
        with Session(self.engine) as session:
            session.add(Message(id=1, content="root", ip="192.0.2.1"))
            session.add(Message(id=2, parent_id=1, content="reply", ip="192.0.2.2"))
            session.add(Message(id=3, parent_id=1, content="hidden reply", ip="192.0.2.3", status="rejected"))
            session.commit()
        public = self.client.get('/api/messages').json()[0]
        self.assertNotIn('ip', public)
        self.assertNotIn('ip', public['replies'][0])
        self.assertEqual(len(public['replies']), 1)
        for action in ('like', 'unlike'):
            response = self.client.post(f'/api/messages/1/{action}')
            self.assertEqual(response.status_code, 200)
            self.assertNotIn('ip', response.json())
            self.assertNotIn('ip', response.json()['replies'][0])
        response = self.client.post('/api/messages', headers=self.reader, json={"content": "new"})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('ip', response.json())
        admin = self.client.get('/api/messages/admin', headers=self.admin).json()
        root = next(msg for msg in admin if msg['id'] == 1)
        self.assertEqual(root['ip'], '192.0.2.1')
        self.assertEqual({r['id'] for r in root['replies']}, {2, 3})


if __name__ == '__main__':
    unittest.main()
