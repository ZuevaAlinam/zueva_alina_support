import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://app:changeme@localhost:5432/zueva_alina")
APP_PORT = int(os.getenv("APP_PORT", "8080"))
SECRET_KEY = os.getenv("SECRET_KEY", "changeme")