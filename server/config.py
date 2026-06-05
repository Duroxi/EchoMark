import os
from dotenv import load_dotenv

load_dotenv()  # 自动读取 .env 文件

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/echomark")
LAST_UPDATE_FILE = os.getenv("LAST_UPDATE_FILE", "/opt/echomark/last_update")
API_KEY_LENGTH = 32
API_KEY_PREFIX = "ek_"
KEY_PREFIX_LEN = 10