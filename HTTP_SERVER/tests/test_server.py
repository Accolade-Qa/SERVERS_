import pytest
from fastapi.testclient import TestClient
from server.app import app
import config
import os
import tempfile

client = TestClient(app)

def test_dashboard():
    response = client.get("/")
    assert response.status_code == 200
    assert "Log File Dashboard" in response.text

def test_upload_without_api_key():
    response = client.post("/upload/", data={"user": "test"}, files={"file": ("test.log", b"test content")})
    assert response.status_code == 422

def test_upload_with_invalid_api_key():
    response = client.post("/upload/", data={"api_key": "invalid", "user": "test"}, files={"file": ("test.log", b"test content")})
    assert response.status_code == 401

def test_upload_valid():
    # Use a filename that matches the required format
    test_filename = "serial_log_864337059682410_Raspberrypi62_20250710_110050.log"
    with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
        f.write("test log content")
        temp_file = f.name

    try:
        with open(temp_file, 'rb') as f:
            response = client.post("/upload/", data={"api_key": config.API_KEY, "user": "test"}, files={"file": (test_filename, f, 'text/plain')})
        assert response.status_code == 200
        assert "uploaded successfully" in response.json()["message"]
    finally:
        os.unlink(temp_file)

def test_download_nonexistent():
    response = client.get("/download/nonexistent.log")
    assert response.status_code == 404

def test_view_nonexistent():
    response = client.get("/view/nonexistent.log")
    assert response.status_code == 404