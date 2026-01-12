# Configuration file for the log server system

import os
import platform

# Detect operating system
IS_WINDOWS = platform.system() == "Windows"
IS_LINUX = platform.system() == "Linux"

# Get user home directory
HOME_DIR = os.path.expanduser("~")

# Server Configuration (these work on both platforms)
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploaded_logs")
TEMP_CHUNKS_DIR = os.getenv("TEMP_CHUNKS_DIR", "temp_chunks")
LOG_FILE = os.getenv("LOG_FILE", "logs/server.log")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///server.db")
TEMPLATES_DIR = os.getenv("TEMPLATES_DIR", "ui")
STATIC_DIR = os.getenv("STATIC_DIR", "ui")
API_KEY = os.getenv("API_KEY", "L2yMnCq8mPBVL076z2YPBQ1MuItdQrrfyRHGaRwyQN8")

# Client Configuration - Cross-platform defaults
if IS_WINDOWS:
    # Windows defaults
    DEFAULT_CLIENT_UPLOAD_DIR = os.path.join(HOME_DIR, "Downloads")
    DEFAULT_UPLOAD_LOG_FILE = os.path.join(HOME_DIR, "Downloads", "serial_log_864337059682410_Raspberrypi62_20250710_110050.log")
    DEFAULT_CRON_LOG_FILE = os.path.join(HOME_DIR, "Downloads", "cron_activity.log")
    DEFAULT_CLIENT_USER = os.environ.get("USERNAME", "windows-user")
elif IS_LINUX:
    # Linux defaults
    DEFAULT_CLIENT_UPLOAD_DIR = os.path.join(HOME_DIR, "Downloads")
    DEFAULT_UPLOAD_LOG_FILE = os.path.join(HOME_DIR, "Downloads", "serial_log_864337059682410_Raspberrypi62_20250710_110050.log")
    DEFAULT_CRON_LOG_FILE = os.path.join(HOME_DIR, "Downloads", "cron_activity.log")
    DEFAULT_CLIENT_USER = os.environ.get("USER", "linux-user")
else:
    # Fallback for other systems
    DEFAULT_CLIENT_UPLOAD_DIR = os.path.join(HOME_DIR, "Downloads")
    DEFAULT_UPLOAD_LOG_FILE = os.path.join(HOME_DIR, "Downloads", "serial_log_864337059682410_Raspberrypi62_20250710_110050.log")
    DEFAULT_CRON_LOG_FILE = os.path.join(HOME_DIR, "Downloads", "cron_activity.log")
    DEFAULT_CLIENT_USER = "unknown-user"

CLIENT_UPLOAD_DIR = os.getenv("CLIENT_UPLOAD_DIR", DEFAULT_CLIENT_UPLOAD_DIR)
SERVER_URL = os.getenv("SERVER_URL", "http://localhost:8000/upload_chunk/")
CLIENT_USER = os.getenv("CLIENT_USER", DEFAULT_CLIENT_USER)
UPLOAD_LOG_FILE = os.getenv("UPLOAD_LOG_FILE", DEFAULT_UPLOAD_LOG_FILE)
CRON_LOG_FILE = os.getenv("CRON_LOG_FILE", DEFAULT_CRON_LOG_FILE)
RETENTION_DAYS = int(os.getenv("RETENTION_DAYS", "7"))
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", str(512 * 1024)))