# Programming Assistant AI Bot - Backend

A FastAPI-based backend service that powers an AI programming assistant with chat capabilities, code analysis, error detection, and multi-modal content processing.

## 🚀 Features

### 🤖 AI Chat Interface
- **Real-time Chat**: Streaming responses with session management
- **Multi-Session Support**: Create and manage multiple conversation sessions
- **Chat History**: Persistent conversation storage with MongoDB

### 🔍 Code Analysis & Assistance
- **Comment-to-Code Generation**: Convert comments into functional code
- **Alternative Code Suggestions**: Generate multiple implementation approaches
- **Error Detection**: AI-powered code error analysis and suggestions
- **Context-Aware Responses**: Leverages conversation history for better suggestions

### 📁 Multi-Modal Content Processing
- **Repository Analysis**: Git repository cloning and analysis
- **PDF Processing**: Extract and analyze PDF documents
- **Web Content**: URL content extraction and processing
- **File Upload Support**: Handle various file types for analysis

### 🔐 Authentication & Security
- **JWT Authentication**: Secure token-based authentication
- **User Management**: Registration, login, and session handling
- **Protected Routes**: Role-based access control

## 🛠️ Tech Stack

- **Framework**: FastAPI with async/await support
- **Database**: MongoDB for chat history and user data
- **Vector Storage**: FAISS for semantic search and embeddings
- **AI Integration**: Ollama LLM (perlbot3:latest model)
- **Authentication**: JWT tokens with bcrypt password hashing
- **File Processing**: PDF loaders, Git integration, web scraping

## 📦 Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd git_check/backend
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Environment Setup**
   ```bash
   # Copy and configure environment variables
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Start the server**
   ```bash
   uvicorn main:app --reload --port 8000
   ```

## ⚙️ Configuration

### Environment Variables
Create a `.env` file with the following variables:

```env
# Database
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=archelon_ai

# JWT Configuration
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# AI Model Configuration
OLLAMA_MODEL=perlbot3:latest
OLLAMA_BASE_URL=http://localhost:11434

# Google Cloud (if using)
GOOGLE_APPLICATION_CREDENTIALS=Config/googlecloud.json
```

## 🏗️ Project Structure

```
backend/
├── main.py                    # FastAPI application entry point
├── config.py                  # Configuration management
├── requirements.txt           # Python dependencies
├── routes/                    # API route definitions
│   ├── auth_routes.py        # Authentication endpoints
│   ├── chatHistoryRoutes.py  # Chat session management
│   ├── chatRoutes.py         # Basic chat functionality
│   ├── chatRoutesTharundi.py # Advanced chat features
│   ├── commentSuggestionRoutes.py # Code suggestion endpoints
│   ├── altCodeRoutes.py      # Alternative code generation
│   ├── errorRoutes.py        # Error detection endpoints
│   └── validateContentRoutes.py # Content validation
├── services/                  # Business logic layer
│   ├── auth/                 # Authentication services
│   ├── chatHistory/          # Chat and LLM integration
│   └── loaders/              # Content processing services
├── models/                    # Database models
├── schemas/                   # Pydantic schemas
├── utils/                     # Utility functions
├── database/                  # Database configuration
├── Controllers/               # Request controllers
└── vectordb/                  # Vector database integration
```

## 📡 API Endpoints

### Authentication
- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `GET /auth/me` - Get current user info

### Chat Management
- `GET /chatHistory/sessions` - List user sessions
- `POST /chatHistory/sessions` - Create new session
- `DELETE /chatHistory/sessions/{id}` - Delete session
- `GET /chatHistory/{session_id}/messages` - Get session messages

### AI Assistance
- `POST /chats/chat` - Send chat message
- `POST /commentCode/suggest` - Generate code from comments
- `POST /validate/error` - Detect code errors
- `POST /alt-code` - Generate alternative implementations

### Content Processing
- `POST /upload` - File upload and analysis
- `POST /process-url` - Web content analysis
- `POST /analyze-repo` - Git repository analysis

## 🚦 Running the Application

### Development Mode
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### With Docker
```bash
# Build image
docker build -t archelon-backend .

# Run container
docker run -p 8000:8000 archelon-backend
```

## 📋 Requirements

- **Python**: 3.9 or higher
- **MongoDB**: 4.4 or higher
- **Ollama**: With perlbot3:latest model installed
- **Memory**: 8GB+ recommended for AI model operations
- **Storage**: 10GB+ for model storage and vector databases

## 🔍 API Documentation

Once the server is running, visit:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## 🧪 Testing

```bash
# Run tests
python -m pytest tests/

# Run specific test
python test.py
```

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is part of the Programming Assistant AI Bot system. Please refer to the main project license for usage terms.

## 🔗 Related Projects

- **Frontend Interface**: `../frontend` - React-based web interface
- **VS Code Extension**: `../VsCodeExtension` - IDE integration
- **Documentation**: Full project documentation

---

Built with ❤️ using FastAPI and modern AI technologies.