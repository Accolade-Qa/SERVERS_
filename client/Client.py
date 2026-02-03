import os
import sys
import time
import json
import requests
import hashlib
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuration (Loads from environment variables or uses defaults)
# SERVER_URL should be the full URL to the upload_chunk endpoint
SERVER_URL = os.getenv("SERVER_URL", "http://localhost:8000/upload_chunk/")
# API_KEY must match the server's API_KEY
API_KEY = os.getenv("API_KEY", "L2yMnCq8mPBVL076z2YPBQ1MuItdQrrfyRHGaRwyQN8")
# CLIENT_USER is used to create a subdirectory on the server
USER = os.getenv("CLIENT_USER", os.environ.get("USERNAME", os.environ.get("USER", "unknown-user")))
# CLIENT_UPLOAD_DIR is the root directory to scan for .log files (e.g., "log/")
UPLOAD_DIR = os.getenv("CLIENT_UPLOAD_DIR", "log")

# These are local bookkeeping files
UPLOAD_LOG = "upload_history.json"
CRON_LOG = "client_activity.log"

# Retention and Chunking
RETENTION_DAYS = int(os.getenv("RETENTION_DAYS", "7"))
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", str(512 * 1024))) # 512KB

def sha256(data):
    return hashlib.sha256(data).hexdigest()

def load_upload_log():
    if os.path.exists(UPLOAD_LOG):
        try:
            with open(UPLOAD_LOG, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"Warning: Corrupted upload log file {UPLOAD_LOG}, starting fresh")
            # Backup the corrupted file
            backup_file = UPLOAD_LOG + ".backup"
            if os.path.exists(backup_file):
                os.remove(backup_file)
            os.rename(UPLOAD_LOG, backup_file)
            return {}
    return {}

def save_upload_log(log_data):
    with open(UPLOAD_LOG, "w") as f:
        json.dump(log_data, f, indent=2)

def is_file_being_written(file_path):
    try:
        with open(file_path, 'a'):
            return False
    except:
        return True

def upload_file(file_path, upload_log):
    if str(file_path) in upload_log:
        return "Already uploaded"

    if is_file_being_written(file_path):
        return "File is still open (write-locked)"

    basic_upload_url = SERVER_URL.replace("upload_chunk", "upload")
    with open(file_path, 'rb') as f:
        files = {'file': (file_path.name, f, 'text/plain')}
        data = {'user': USER}
        headers = {"X-API-Key": API_KEY}
        try:
            res = requests.post(basic_upload_url, files=files, data=data, headers=headers)
            if res.status_code == 200:
                upload_log[str(file_path)] = str(datetime.now())
                return "Uploaded"
            else:
                return f"Failed (HTTP {res.status_code})"
        except Exception as e:
            return f"Failed ({e})"
        
def upload_file_chunked(file_path, upload_log):
    if str(file_path) in upload_log:
        return "Already uploaded"

    if is_file_being_written(file_path):
        return "File is still open (write-locked)"

    # Use the original filename as file_id (it should already be validated)
    file_id = file_path.name
    file_size = os.path.getsize(file_path)
    total_chunks = (file_size + CHUNK_SIZE - 1) // CHUNK_SIZE

    with open(file_path, 'rb') as f:
        for i in range(total_chunks):
            chunk = f.read(CHUNK_SIZE)
            headers = {
                "X-File-ID": file_id,
                "X-Chunk-Index": str(i),
                "X-Total-Chunks": str(total_chunks),
                "X-User": USER,
                "X-Chunk-Hash": sha256(chunk),
                "X-API-Key": API_KEY
            }
            files = {'chunk': ("chunk", chunk)}
            try:
                r = requests.post(SERVER_URL, headers=headers, files=files)
                r.raise_for_status()
            except Exception as e:
                return f"Failed chunk {i}: {e}"

    upload_log[str(file_path)] = str(datetime.now())
    return "Uploaded"

def delete_old_files(upload_log):
    now = datetime.now()
    deleted = []
    for file_str in list(upload_log):
        file_path = Path(file_str)
        if file_path.exists() and (now - datetime.fromtimestamp(file_path.stat().st_mtime)).days >= RETENTION_DAYS:
            try:
                file_path.unlink()
                deleted.append(file_str)
                del upload_log[file_str]
            except:
                pass
    return deleted

def log_activity(message):
    with open(CRON_LOG, "a") as logf:
        logf.write(f"{datetime.now()}: {message}\n")

def main():
    upload_log = load_upload_log()
    for file_path in Path(UPLOAD_DIR).rglob("*.log"):
        result = upload_file_chunked(file_path, upload_log)
        log_activity(f"{file_path.name}: {result}")
    for f in delete_old_files(upload_log):
        log_activity(f"Deleted old file: {f}")
    save_upload_log(upload_log)

if __name__ == "__main__":
    main()