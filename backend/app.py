from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Header, Depends
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
import shutil
import uuid
import hashlib
import zipfile
import tempfile
from loguru import logger
from . import config

app = FastAPI()

# Backend is now a pure API server.
# React frontend is served separately (via Vite in dev, or build artifacts in prod).


UPLOAD_DIR = config.UPLOAD_DIR
TEMP_CHUNKS_DIR = config.TEMP_CHUNKS_DIR
LOG_FILE = config.LOG_FILE
DATABASE_URL = config.DATABASE_URL
API_KEY = config.API_KEY

logger.add(LOG_FILE, rotation="1 MB", retention="10 days", level="INFO")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(TEMP_CHUNKS_DIR, exist_ok=True)
os.makedirs("logs", exist_ok=True)

Base = declarative_base()
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)

class LogEntry(Base):
    __tablename__ = "log_entries"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, unique=True)
    original_filename = Column(String)
    user = Column(String)
    timestamp = Column(DateTime)

Base.metadata.create_all(bind=engine)

def verify_api_key(x_api_key: str = Header(None, alias="X-API-Key"), api_key: str = Form(None)):
    key = x_api_key or api_key
    if not key or key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return key

@app.post("/upload/")
async def upload_log_file(
    api_key: str = Form(...),
    user: str = Form(...),
    file: UploadFile = File(...)
):
    logger.info(f"Upload attempt - User: {user}, File: {file.filename if file else 'None'}, API Key provided: {bool(api_key)}")

    if not api_key or api_key != API_KEY:
        logger.warning(f"Invalid API key attempt from user: {user}")
        raise HTTPException(status_code=401, detail="Invalid API Key")
    
    # Validate filename format: must start with "serial_log_" and end with ".log"
    if not file.filename or not (file.filename.startswith("serial_log_") and file.filename.endswith(".log")):
        logger.warning(f"Rejected invalid filename format: {file.filename}")
        raise HTTPException(status_code=400, detail="Filename must be in format: serial_log_[serial]_[device]_[date]_[time].log")

    # Create folder structure: uploaded_logs/{username}/{date}/
    current_date = datetime.utcnow().strftime("%Y-%m-%d")
    user_dir = os.path.join(UPLOAD_DIR, user)
    date_dir = os.path.join(user_dir, current_date)
    os.makedirs(date_dir, exist_ok=True)

    # Use original filename directly (already validated)
    file_path = os.path.join(date_dir, file.filename)

    # Check if file already exists
    if os.path.exists(file_path):
        logger.warning(f"File already exists: {file_path}")
        raise HTTPException(status_code=409, detail="File with this name already exists")

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    db = SessionLocal()
    try:
        entry = LogEntry(
            filename=os.path.join(user, current_date, file.filename),
            original_filename=file.filename,
            user=user,
            timestamp=datetime.utcnow()
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)
        logger.info(f"Uploaded by {user}: {file.filename} -> {file_path}")
        return {"message": "File uploaded successfully", "metadata": {
            "filename": file.filename,
            "user": user,
            "date": current_date,
            "timestamp": entry.timestamp.isoformat()
        }}
    finally:
        db.close()

@app.post("/upload_chunk/")
async def upload_chunk(
    chunk: UploadFile,
    x_file_id: str = Header(...),
    x_chunk_index: int = Header(...),
    x_total_chunks: int = Header(...),
    x_chunk_hash: str = Header(...),
    x_user: str = Header(...),
    x_api_key: str = Header(...)
):
    # Validate filename format for chunked uploads
    if not x_file_id or not (x_file_id.startswith("serial_log_") and x_file_id.endswith(".log")):
        raise HTTPException(status_code=400, detail="Filename must be in format: serial_log_[serial]_[device]_[date]_[time].log")

    file_subdir = os.path.join(TEMP_CHUNKS_DIR, x_file_id)
    os.makedirs(file_subdir, exist_ok=True)
    chunk_path = os.path.join(file_subdir, f"{x_chunk_index}.part")

    content = await chunk.read()
    if hashlib.sha256(content).hexdigest() != x_chunk_hash:
        raise HTTPException(status_code=400, detail="Hash mismatch")

    with open(chunk_path, "wb") as f:
        f.write(content)

    parts = sorted(os.listdir(file_subdir), key=lambda x: int(x.split(".")[0]))
    if len(parts) == x_total_chunks:
        # Create folder structure for final file
        current_date = datetime.utcnow().strftime("%Y-%m-%d")
        user_dir = os.path.join(UPLOAD_DIR, x_user)
        date_dir = os.path.join(user_dir, current_date)
        os.makedirs(date_dir, exist_ok=True)
        
        final_path = os.path.join(date_dir, x_file_id)
        
        # Check if file already exists
        if os.path.exists(final_path):
            shutil.rmtree(file_subdir)
            raise HTTPException(status_code=409, detail="File with this name already exists")
        
        with open(final_path, "wb") as final:
            for part in parts:
                with open(os.path.join(file_subdir, part), "rb") as p:
                    final.write(p.read())
        shutil.rmtree(file_subdir)
        db = SessionLocal()
        try:
            entry = LogEntry(
                filename=os.path.join(x_user, current_date, x_file_id),
                original_filename=x_file_id,
                user=x_user,
                timestamp=datetime.utcnow()
            )
            db.add(entry)
            db.commit()
        finally:
            db.close()
        return {"status": "complete", "message": f"{x_file_id} fully uploaded"}

    return {"status": "incomplete", "chunk_index": x_chunk_index}

@app.get("/")
def api_root():
    return {
        "name": "Log Management API",
        "version": "1.0.0",
        "status": "online",
        "endpoints": {
            "logs": "/api/logs",
            "view": "/view/{id}",
            "delete": "/delete/{id}",
            "download": "/download/{id}"
        }
    }

@app.get("/api/logs")
def get_logs():
    db = SessionLocal()
    try:
        logs = db.query(LogEntry).order_by(LogEntry.timestamp.desc()).all()
        return [
            {
                "id": log.id,
                "user": log.user,
                "filename": log.filename,
                "original_filename": log.original_filename,
                "timestamp": log.timestamp.isoformat() if log.timestamp else None,
                "size": os.path.getsize(os.path.join(UPLOAD_DIR, log.filename)) if os.path.exists(os.path.join(UPLOAD_DIR, log.filename)) else 0
            }
            for log in logs
        ]
    finally:
        db.close()

@app.get("/view/{log_id}")
def view_log_file(log_id: int, offset: int = 0, limit: int = 102400): # Default limit 100KB
    db = SessionLocal()
    try:
        log = db.query(LogEntry).filter(LogEntry.id == log_id).first()
        if not log:
            raise HTTPException(status_code=404, detail="Log entry not found")
        
        file_path = os.path.join(UPLOAD_DIR, log.filename)
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found on disk")

        file_size = os.path.getsize(file_path)
        
        if offset >= file_size:
            return {
                "id": log.id,
                "filename": log.original_filename,
                "content": "",
                "next_offset": None,
                "total_size": file_size
            }

        # Read specific chunk
        content = ""
        actual_limit = min(limit, file_size - offset)
        
        # We use binary mode and decode with errors='replace' for robustness on chunks
        # because a chunk might cut through a multi-byte character
        with open(file_path, "rb") as f:
            f.seek(offset)
            chunk = f.read(actual_limit)
            content = chunk.decode('utf-8', errors='replace')

        next_offset = offset + actual_limit
        if next_offset >= file_size:
            next_offset = None

        return {
            "id": log.id,
            "filename": log.original_filename,
            "user": log.user,
            "content": content,
            "next_offset": next_offset,
            "total_size": file_size
        }
    finally:
        db.close()

@app.get("/download/{log_id}")
def download_log_file(log_id: int):
    db = SessionLocal()
    try:
        log = db.query(LogEntry).filter(LogEntry.id == log_id).first()
        if not log:
            raise HTTPException(status_code=404, detail="Log entry not found")
        
        file_path = os.path.join(UPLOAD_DIR, log.filename)
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
            
        # Ensure filename is safe for headers
        from urllib.parse import quote
        encoded_filename = quote(log.original_filename)
        
        return FileResponse(
            path=file_path, 
            filename=log.original_filename, 
            media_type='text/plain',
            headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"}
        )
    finally:
        db.close()

@app.delete("/delete/{log_id}")
async def delete_log_file(log_id: int):
    db = SessionLocal()
    try:
        log = db.query(LogEntry).filter(LogEntry.id == log_id).first()
        if not log:
            raise HTTPException(status_code=404, detail="Log entry not found")
        
        file_path = os.path.join(UPLOAD_DIR, log.filename)
        
        # 1. Delete file from disk
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f"Deleted file from disk: {file_path}")
            except Exception as e:
                logger.error(f"Error deleting file {file_path}: {e}")
                # Continue anyway to clean up DB
        
        # 2. Delete entry from database
        db.delete(log)
        db.commit()
        logger.info(f"Deleted database entry for ID: {log_id}")
        
        return {"message": "Log deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting log: {e}")
        raise HTTPException(status_code=500, detail="Error deleting log")
    finally:
        db.close()
@app.get("/download_folder/")
def download_folder(user: str = None, date: str = None):
    db = SessionLocal()
    try:
        query = db.query(LogEntry)
        if user:
            query = query.filter(LogEntry.user == user)
        
        logs = query.all()
        
        target_logs = []
        if date:
            for log in logs:
                log_date = log.timestamp.strftime("%Y-%m-%d") if log.timestamp else "Unknown"
                if log_date == date:
                    target_logs.append(log)
        else:
            target_logs = logs

        if not target_logs:
            raise HTTPException(status_code=404, detail="No logs found for this folder")

        # Create a temporary zip file
        fd, temp_path = tempfile.mkstemp(suffix='.zip')
        os.close(fd)
        
        with zipfile.ZipFile(temp_path, 'w') as zipf:
            for log in target_logs:
                file_path = os.path.join(UPLOAD_DIR, log.filename)
                if os.path.exists(file_path):
                    zipf.write(file_path, arcname=log.original_filename)

        return FileResponse(
            path=temp_path,
            filename=f"{user or 'all'}_{date or 'logs'}.zip",
            media_type='application/zip'
        )
    finally:
        db.close()

@app.delete("/delete_folder/")
def delete_folder(user: str = None, date: str = None):
    db = SessionLocal()
    try:
        query = db.query(LogEntry)
        if user:
            query = query.filter(LogEntry.user == user)
        
        logs = query.all()
        target_logs = []
        if date:
            for log in logs:
                log_date = log.timestamp.strftime("%Y-%m-%d") if log.timestamp else "Unknown"
                if log_date == date:
                    target_logs.append(log)
        else:
            target_logs = logs

        deleted_count = 0
        for log in target_logs:
            file_path = os.path.join(UPLOAD_DIR, log.filename)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except:
                    pass
            db.delete(log)
            deleted_count += 1
        
        db.commit()
        return {"message": f"Successfully deleted {deleted_count} logs"}
    finally:
        db.close()
