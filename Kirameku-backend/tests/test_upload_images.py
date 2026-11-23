import unittest
from io import BytesIO
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient
from PIL import Image

from app.config import OSS_CUSTOM_DOMAIN, OSS_PREFIX
from app.deps import get_current_user
from app.main import app
from app.schemas.album import AlbumCreate
from app.schemas.chatter import ChatterCreate
from app.schemas.post import PostCreate
from app.utils.media import MEDIA_PATH


class UploadImageTests(unittest.TestCase):
    def test_upload_returns_a_readable_image_path(self):
        buf = BytesIO()
        Image.new("RGB", (3, 2)).save(buf, "PNG")
        image = buf.getvalue()
        bucket = Mock()
        bucket.get_object.return_value = BytesIO(image)
        app.dependency_overrides[get_current_user] = lambda: {"admin": True}
        self.addCleanup(app.dependency_overrides.pop, get_current_user)
        with patch("app.api.upload._get_bucket", return_value=bucket):
            client = TestClient(app)
            result = client.post("/api/upload/image", files={"file": ("photo", image, "image/png")})
            self.assertEqual(result.status_code, 200)
            path = result.json()["url"]
            self.assertTrue(path.startswith(MEDIA_PATH))
            self.assertTrue(path.endswith(".png"))
            key = OSS_PREFIX + path.removeprefix(MEDIA_PATH)
            bucket.put_object.assert_called_once_with(key, image)
            response = client.get(path)
            self.assertEqual(response.headers["content-type"], "image/png")
            self.assertEqual(response.content, image)
            self.assertEqual(client.get(MEDIA_PATH + "other.png").status_code, 404)
            bucket.get_object.assert_called_once_with(key)

    def test_existing_references_and_external_images(self):
        name = "ab" * 16 + ".jpg"
        old = OSS_CUSTOM_DOMAIN.strip().rstrip("/") + "/" + OSS_PREFIX + name
        new = MEDIA_PATH + name
        external = "https://example.com/photo.jpg"
        self.assertEqual(AlbumCreate(title="a", cover=" " + old).cover, new)
        self.assertEqual(ChatterCreate(content="", images=[old, external]).images, [new, external])
        post = PostCreate(title="t", slug="t", content=f"![photo]({old})\n{external}")
        self.assertEqual(post.content, f"![photo]({new})\n{external}")
