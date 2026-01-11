# Log File Upload Server

A comprehensive FastAPI-based system for centralized log file collection, management, and analysis from distributed devices.

## Table of Contents

- [🚀 Features](#-features)
- [📁 Project Structure](#-project-structure)
- [🛠 Installation](#-installation)
- [⚙️ Configuration](#️-configuration)
- [🎯 Usage](#-usage)
- [🔌 API Endpoints](#-api-endpoints)
- [🧪 Testing](#-testing)
- [🔒 Security Features](#-security-features)
- [📊 Database Schema](#-database-schema)
- [🚀 Deployment](#-deployment)
- [🐛 Troubleshooting](#-troubleshooting)
- [🤝 Contributing](#-contributing)
- [📄 License](#-license)
- [📞 Support](#-support)

## 🚀 Features

- **Secure File Uploads**: API key authenticated uploads with chunked transfer support
- **Web Dashboard**: Modern responsive interface for log management
- **Real-time Monitoring**: Live log viewing with syntax highlighting
- **Database Storage**: SQLite-based metadata storage with SQLAlchemy ORM
- **Automated Client**: Python client for automated log collection from IoT devices
- **RESTful API**: Complete REST API for programmatic access
- **File Validation**: Strict .log file type validation
- **Error Handling**: Comprehensive error handling and logging
- **Responsive Design**: Mobile-friendly web interface with Tailwind CSS

## 📁 Project Structure

```
├── server/
│   ├── __init__.py
│   └── app.py              # FastAPI application with all endpoints
├── client/
│   └── Client.py           # Automated log upload client
├── tests/
│   └── test_server.py     # Comprehensive test suite
├── static/
│   ├── css/
│   │   └── index.css       # Custom styling
│   └── js/
│     └── index.js          # Client-side functionality
├── templates/
│   ├── dashboard.html      # Main web interface
│   └── view_log.html       # Log viewer interface
├── config.py               # Configuration management
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies with pinned versions
└── README.md               # This documentation
```

## 🛠 Installation

### Prerequisites
- Python 3.9+
- pip package manager

### Setup Steps

1. **Clone/Download the project**
   ```bash
   cd /path/to/project
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment** (optional)
   ```bash
   # Set custom API key
   export API_KEY="your-custom-key"

   # Configure upload directory
   export UPLOAD_DIR="/custom/path/logs"

   # Other options available in config.py
   ```

4. **Run the server**
   ```bash
   python main.py
   ```

5. **Access the application**
   - Web Interface: http://localhost:8000
   - API Documentation: http://localhost:8000/docs (Swagger UI)

## ⚙️ Configuration

The application uses environment variables for configuration. All settings have sensible defaults:

| Variable | Default | Description |
|----------|---------|-------------|
| `API_KEY` | Auto-generated | Authentication key for uploads |
| `UPLOAD_DIR` | `uploaded_logs` | Directory for uploaded files |
| `TEMP_CHUNKS_DIR` | `temp_chunks` | Temporary chunk storage |
| `LOG_FILE` | `logs/server.log` | Application log file |
| `DATABASE_URL` | `sqlite:///server.db` | Database connection string |
| `TEMPLATES_DIR` | `templates` | HTML templates directory |

## 🎯 Usage

### Web Interface

1. **Access Dashboard**: http://localhost:8000
2. **Upload Logs**:
   - Click "📤 Upload New Log"
   - API Key is pre-filled (change if needed)
   - Enter a username
   - Select a .log file
   - Click "Upload"
3. **View Logs**:
   - Browse uploaded files in the table
   - Click "View" for syntax-highlighted content
   - Click "Download" for file download

### Client Script

Run automated log collection on client devices:

```bash
python client/Client.py
```

Configure client settings via environment variables:
- `CLIENT_UPLOAD_DIR`: Source directory for logs
- `SERVER_URL`: Server endpoint URL
- `CLIENT_USER`: Device identifier
- `UPLOAD_LOG_FILE`: Local upload tracking file

### API Usage

#### Upload Single File
```bash
curl -X POST "http://localhost:8000/upload/" \
  -F "api_key=L2yMnCq8mPBVL076z2YPBQ1MuItdQrrfyRHGaRwyQN8" \
  -F "user=testuser" \
  -F "file=@example.log"
```

#### Upload in Chunks (for large files)
```bash
# Client handles chunking automatically
python client/Client.py
```

#### View Dashboard
```bash
curl http://localhost:8000/
```

## 🔌 API Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/` | Web dashboard | No |
| POST | `/upload/` | Single file upload | API Key |
| POST | `/upload_chunk/` | Chunked file upload | API Key |
| GET | `/view/{filename}` | View log content | No |
| GET | `/download/{filename}` | Download log file | No |

### Authentication

- **API Key**: Required for upload endpoints
- **Current Key**: `L2yMnCq8mPBVL076z2YPBQ1MuItdQrrfyRHGaRwyQN8`
- **Header**: `X-API-Key: <key>` (for chunked uploads)
- **Form Field**: `api_key=<key>` (for web uploads)

## 🧪 Testing

Run the test suite:

```bash
pytest tests/
```

Tests cover:
- API endpoint functionality
- Authentication
- File upload validation
- Error handling

## 🔒 Security Features

- **API Key Authentication**: Cryptographically secure keys
- **File Type Validation**: Only .log files accepted
- **Input Sanitization**: Proper validation of all inputs
- **Secure Headers**: FastAPI security headers
- **Logging**: Comprehensive audit logging

## 📊 Database Schema

### LogEntry Table
- `id`: Primary key
- `filename`: Unique filename
- `original_filename`: Original uploaded name
- `user`: Uploading user
- `timestamp`: Upload timestamp

## 🚀 Deployment

### Production Considerations

1. **Change API Key**: Generate a new secure key for production
2. **Database**: Consider PostgreSQL for production workloads
3. **File Storage**: Use cloud storage (S3, etc.) for scalability
4. **HTTPS**: Enable SSL/TLS in production
5. **Monitoring**: Add application monitoring and alerts

### Environment Variables for Production

```bash
export API_KEY="your-production-key"
export DATABASE_URL="postgresql://user:pass@host:port/db"
export UPLOAD_DIR="/secure/upload/path"
```

## 🐛 Troubleshooting

### Common Issues

**422 Unprocessable Entity on Upload**
- Ensure all required fields are filled
- Check API key is correct
- Verify file is .log format

**401 Unauthorized**
- Verify API key matches server configuration
- Check for typos in key

**404 File Not Found**
- Ensure file exists in upload directory
- Check filename in URL

### Logs

Application logs are stored in `logs/server.log`. Check for detailed error information.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

This project is open source. Feel free to use and modify as needed.

## 📞 Support

For issues or questions:
1. Check the logs in `logs/server.log`
2. Review the API documentation at `/docs`
3. Ensure all dependencies are installed correctly

---

**Built with**: FastAPI, SQLAlchemy, Jinja2, Tailwind CSS, Alpine.js
**Python Version**: 3.9+
**Database**: SQLite (configurable)