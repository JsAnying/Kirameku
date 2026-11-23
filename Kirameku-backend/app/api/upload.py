import uuid
from io import BytesIO

import oss2
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import StreamingResponse
from PIL import Image

from app.deps import get_current_user
from app.config import (
    OSS_ACCESS_KEY_ID,
    OSS_ACCESS_KEY_SECRET,
    OSS_BUCKET_NAME,
    OSS_ENDPOINT,
    OSS_PREFIX,
)
from app.utils.media import MEDIA_PATH, UPLOAD_NAME

router = APIRouter(tags=["上传"])

IMAGE_EXTENSIONS = {
    "image/jpeg": "jpg", "image/png": "png", "image/webp": "webp",
    "image/gif": "gif", "image/svg+xml": "svg",
}
MAX_SIZE = 10 * 1024 * 1024  # 10MB


def _get_bucket():
    auth = oss2.Auth(OSS_ACCESS_KEY_ID, OSS_ACCESS_KEY_SECRET)
    endpoint = OSS_ENDPOINT if "://" in OSS_ENDPOINT else f"https://{OSS_ENDPOINT}"
    return oss2.Bucket(auth, endpoint, OSS_BUCKET_NAME)


@router.get(MEDIA_PATH + "{filename}")
def read_image(filename: str):
    if not UPLOAD_NAME.fullmatch(filename):
        raise HTTPException(404, "图片不存在")
    try:
        obj = _get_bucket().get_object(OSS_PREFIX + filename)
    except oss2.exceptions.NoSuchKey:
        raise HTTPException(404, "图片不存在")
    except oss2.exceptions.OssError:
        raise HTTPException(502, "图片存储服务暂时不可用")

    def chunks():
        with obj:
            while chunk := obj.read(64 * 1024):
                yield chunk

    extension = filename.rsplit(".", 1)[1].lower()
    media_type = {"jpg": "image/jpeg", "svg": "image/svg+xml"}.get(extension, f"image/{extension}")
    return StreamingResponse(chunks(), media_type=media_type, headers={
        "Cache-Control": "public, max-age=31536000, immutable",
        "X-Content-Type-Options": "nosniff",
        "Content-Security-Policy": "sandbox; default-src 'none'; style-src 'unsafe-inline'",
    })


@router.post("/api/upload/image")
async def upload_image(
    file: UploadFile = File(...),
    _: dict = Depends(get_current_user),
):
    if file.content_type not in IMAGE_EXTENSIONS:
        raise HTTPException(400, f"不支持的文件类型: {file.content_type}")

    content = await file.read()
    if len(content) > MAX_SIZE:
        raise HTTPException(400, "文件大小不能超过 10MB")

    # 检测方向
    orientation = "landscape"
    try:
        img = Image.open(BytesIO(content))
        w, h = img.size
        orientation = "landscape" if w >= h else "portrait"
    except Exception:
        pass

    # 生成 OSS 路径
    ext = IMAGE_EXTENSIONS[file.content_type]
    filename = f"{uuid.uuid4().hex}.{ext}"
    oss_key = f"{OSS_PREFIX}{filename}"

    # 上传到 OSS
    bucket = _get_bucket()
    bucket.put_object(oss_key, content)

    url = MEDIA_PATH + filename
    return {"url": url, "orientation": orientation}
