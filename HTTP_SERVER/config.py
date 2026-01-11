# Configuration file for the log server system

import os

# Server Configuration
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploaded_logs")
TEMP_CHUNKS_DIR = os.getenv("TEMP_CHUNKS_DIR", "temp_chunks")
LOG_FILE = os.getenv("LOG_FILE", "logs/server.log")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///server.db")
TEMPLATES_DIR = os.getenv("TEMPLATES_DIR", "templates")
API_KEY = os.getenv("API_KEY", "L2yMnCq8mPBVL076z2YPBQ1MuItdQrrfyRHGaRwyQN8")

# Client Configuration
CLIENT_UPLOAD_DIR = os.getenv("CLIENT_UPLOAD_DIR", "/home/pi/logs_to_upload")
SERVER_URL = os.getenv("SERVER_URL", "http://localhost:8000/upload_chunk/")
CLIENT_USER = os.getenv("CLIENT_USER", "pi-board-01")
UPLOAD_LOG_FILE = os.getenv("UPLOAD_LOG_FILE", "/home/pi/upload_log.json")
CRON_LOG_FILE = os.getenv("CRON_LOG_FILE", "/home/pi/cron_activity.log")
RETENTION_DAYS = int(os.getenv("RETENTION_DAYS", "7"))
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", str(512 * 1024)))