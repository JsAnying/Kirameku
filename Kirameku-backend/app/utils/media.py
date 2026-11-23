import re
from typing import Annotated

from pydantic import AfterValidator

from app.config import OSS_CUSTOM_DOMAIN, OSS_PREFIX


MEDIA_PATH = "/api/media/"
UPLOAD_NAME = re.compile(r"[0-9a-f]{32}\.(?:jpe?g|png|webp|gif|svg)", re.IGNORECASE | re.ASCII)
_oss_base = OSS_CUSTOM_DOMAIN.strip().rstrip("/") + "/" + OSS_PREFIX
_legacy_image = re.compile(
    r"""(?P<before>!\[[^\]\n]*\]\(\s*<?|<img\b[^>]*?\bsrc\s*=\s*["'])"""
    + re.escape(_oss_base) + "(" + UPLOAD_NAME.pattern + r""")(?=[>"')\s])""",
    re.IGNORECASE | re.ASCII,
)


def image_url(value: str) -> str:
    url = value.strip()
    if url.startswith(_oss_base):
        name = url[len(_oss_base):]
        if UPLOAD_NAME.fullmatch(name):
            return MEDIA_PATH + name
    return url


def _inline_images(content: str) -> str:
    return _legacy_image.sub(lambda m: m["before"] + MEDIA_PATH + m[2], content)


ImageUrl = Annotated[str, AfterValidator(image_url)]
ImageContent = Annotated[str, AfterValidator(_inline_images)]
