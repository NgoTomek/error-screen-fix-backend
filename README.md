# Error Screen Fix - Backend

A Flask-based backend API for the Error Screen Fix platform that provides AI-powered error analysis and enterprise features.

## 🚀 Features

- **AI Error Analysis**: Process error screenshots and provide comprehensive solutions
- **User Management**: Authentication, profiles, and user data
- **RESTful API**: Clean, well-documented API endpoints
- **Database Integration**: SQLite database with SQLAlchemy ORM
- **CORS Support**: Cross-origin requests enabled
- **File Processing**: Image upload and base64 processing
- **Error Handling**: Comprehensive error handling and validation

## 🛠️ Tech Stack

- **Flask** - Web framework
- **SQLAlchemy** - Database ORM
- **Flask-CORS** - Cross-origin resource sharing
- **Pillow** - Image processing
- **Requests** - HTTP client for external APIs
- **SQLite** - Database

## 📦 Installation

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python src/main.py
```

## 🔧 Configuration

The application runs on `http://localhost:8081` by default. You can modify the port in `src/main.py`:

```python
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8081, debug=True)
```

## 📚 API Endpoints

### Core Features
- `POST /api/analyze-error` - Analyze error screenshots
- `GET /api/users` - Get all users
- `POST /api/users` - Create new user
- `GET /api/users/<id>` - Get specific user
- `PUT /api/users/<id>` - Update user
- `DELETE /api/users/<id>` - Delete user

### Error Analysis
```bash
# Example request
curl -X POST http://localhost:8081/api/analyze-error \
  -H "Content-Type: application/json" \
  -d '{
    "image": "data:image/png;base64,iVBORw0KGgo...",
    "context": "Additional error context"
  }'
```

## 🗄️ Database Schema

The application uses SQLite with the following tables:
- **users** - User accounts and profiles
- **error_analyses** - Error analysis history
- **solutions** - AI-generated solutions
- **feedback** - User feedback on solutions

## 🚀 Deployment

### Local Development
```bash
python src/main.py
```

### Production Deployment
1. Set environment variables for production
2. Use a production WSGI server like Gunicorn
3. Configure proper database settings
4. Set up reverse proxy (nginx)

### Docker Deployment
```bash
# Build image
docker build -t error-screen-fix-backend .

# Run container
docker run -p 8081:8081 error-screen-fix-backend
```

## 🔒 Security

- Input validation on all endpoints
- CORS configuration for frontend integration
- Error handling to prevent information leakage
- Database parameterized queries to prevent SQL injection

## 📁 Project Structure

```
src/
├── main.py              # Application entry point
├── models/
│   └── user.py         # Database models
├── routes/
│   ├── user.py         # User management routes
│   └── error_fix.py    # Error analysis routes
└── database/           # SQLite database files
```

## 🧪 Testing

```bash
# Test API endpoints
curl http://localhost:8081/api/users

# Test error analysis
curl -X POST http://localhost:8081/api/analyze-error \
  -H "Content-Type: application/json" \
  -d '{"image": "base64_image_data"}'
```

## 📄 License

MIT License - see LICENSE file for details

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new features
5. Submit a pull request

## 📞 Support

For support and questions, please open an issue in the GitHub repository.

## 🔗 Frontend Integration

This backend is designed to work with the Error Screen Fix React frontend:
- Repository: [error-screen-fix-frontend](../error-screen-fix-frontend)
- Update the `API_BASE_URL` in the frontend to point to this backend

