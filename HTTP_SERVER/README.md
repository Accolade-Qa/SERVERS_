# Log Management System

A modern, full-stack application for managing and viewing Raspberry Pi log files.

## 🏗️ Project Structure

```text
HTTP_SERVER/
├── backend/            # FastAPI Pure API Backend
│   ├── app.py          # Log processing endpoints
│   ├── config.py       # Configuration loader (uses .env)
│   └── server.db       # Log metadata database (created on run)
├── frontend/           # React + Vite + Tailwind Frontend
│   ├── src/            # UI components (Explorer, Modal)
│   ├── index.html      # Frontend entry
│   └── package.json    # React dependencies
├── client/             # Standalone Python upload client
├── main.py             # Backend entry point
├── .env                # Local configuration (Private)
└── requirements.txt    # Python dependencies
```

## ⚙️ Configuration

Create a `.env` file in the root directory (already done for you) with the following:
- `API_KEY`: Secret key for uploading logs.
- `UPLOAD_DIR`: Path to store log files.
- `LOG_FILE`: Path to the server's own activity logs.

## 🚀 How to Run

### 1. Backend Server
From the project root:
```powershell
# Install python dependencies
pip install -r requirements.txt

# Start the server
python main.py
```

### 2. Frontend Development
From the project root:
```powershell
# Go to frontend folder
cd frontend

# Install react dependencies
npm install

# Start development server
npm run dev
```

The UI will be available at `http://localhost:5173`.
The API will be available at `http://localhost:8000`.

## 🧹 Maintenance (PowerShell Cleanup)
To remove legacy folders if they still exist:
```powershell
Remove-Item -Recurse -Force "ui", "static", "templates", "node_modules"
```