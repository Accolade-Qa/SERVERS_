from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Header, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
import shutil
import uuid
import hashlib
from loguru import logger
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import config

app = FastAPI()

app.mount("/static", StaticFiles(directory=config.STATIC_DIR), name="static")


UPLOAD_DIR = config.UPLOAD_DIR
TEMP_CHUNKS_DIR = config.TEMP_CHUNKS_DIR
LOG_FILE = config.LOG_FILE
DATABASE_URL = config.DATABASE_URL
API_KEY = config.API_KEY
templates = Jinja2Templates(directory=config.TEMPLATES_DIR)

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

@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    db = SessionLocal()
    try:
        # Get all log entries from database
        logs = db.query(LogEntry).order_by(LogEntry.timestamp.desc()).all()
        
        # Build folder structure from DB entries instead of disk for consistency
        folder_structure = {}
        for log in logs:
            user = log.user or "Unknown User"
            
            # Normalize and split filename
            clean_filename = log.filename.replace('\\', '/').strip('/')
            parts = clean_filename.split('/')
            
            # Extract date if possible (assumes user/date/file)
            # If structure is different, we fallback to log.timestamp date
            if len(parts) >= 2:
                # If parts[0] is equal to user, then parts[1] is likely the date
                # otherwise use timestamp as date fallback
                date = parts[1] if len(parts) >= 3 else log.timestamp.strftime("%Y-%m-%d")
            else:
                date = log.timestamp.strftime("%Y-%m-%d") if log.timestamp else "Unknown Date"

            if user not in folder_structure:
                folder_structure[user] = {}
            if date not in folder_structure[user]:
                folder_structure[user][date] = []
            
            folder_structure[user][date].append(log)

        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "logs": logs,
            "folder_structure": folder_structure
        })
    finally:
        db.close()

@app.get("/view/{log_id}")
def view_log_file(log_id: int):
    db = SessionLocal()
    try:
        log = db.query(LogEntry).filter(LogEntry.id == log_id).first()
        if not log:
            raise HTTPException(status_code=404, detail="Log entry not found")
        
        file_path = os.path.join(UPLOAD_DIR, log.filename)
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found on disk")

        file_stats = os.stat(file_path)
        with open(file_path, "r") as f:
            content = f.read()

        return {
            "id": log.id,
            "filename": log.original_filename,
            "user": log.user,
            "content": content,
            "size": file_stats.st_size,
            "modified": file_stats.st_mtime
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
        return FileResponse(path=file_path, filename=log.original_filename, media_type='text/plain')
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
