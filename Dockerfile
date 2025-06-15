# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/

# Expose port
EXPOSE 8080

# Set environment variables
ENV PYTHONPATH=/app
ENV FLASK_APP=src/main.py
ENV GEMINI_API_KEY="AIzaSyCKl7FvCPoNBklNf1klaImZIbcGFXuTlYY"

# Run the application
CMD ["python", "src/main.py"]

