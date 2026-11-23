import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env", override=True)
# 显式启用时，用生产配置覆盖基础 .env；本地默认不读取生产配置。
if os.environ.get("KIRAMEKU_ENV") == "production":
    production_env = BASE_DIR / ".env.production"
    if not production_env.is_file():
        raise RuntimeError("KIRAMEKU_ENV=production requires .env.production")
    load_dotenv(production_env, override=True)

DATABASE_URL = os.environ["DATABASE_URL"]
SECRET_KEY = os.environ["SECRET_KEY"]
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 72

CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173,https://boke.hiromu.top").split(",")

# GitHub OAuth
GITHUB_CLIENT_ID = os.environ.get("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET = os.environ.get("GITHUB_CLIENT_SECRET", "")

# 阿里云 OSS 配置
OSS_ACCESS_KEY_ID = os.environ["OSS_ACCESS_KEY_ID"]
OSS_ACCESS_KEY_SECRET = os.environ["OSS_ACCESS_KEY_SECRET"]
OSS_BUCKET_NAME = os.environ["OSS_BUCKET_NAME"]
OSS_ENDPOINT = os.environ["OSS_ENDPOINT"]
OSS_CUSTOM_DOMAIN = os.environ["OSS_CUSTOM_DOMAIN"]
OSS_PREFIX = os.environ["OSS_PREFIX"]
