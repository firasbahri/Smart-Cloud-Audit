FROM python:3.11-slim

WORKDIR /app

# Convert CRLF → LF before anything else
RUN apt-get update && apt-get install -y --no-install-recommends dos2unix && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Fix Windows line endings on all Python files
RUN find /app -name "*.py" -exec dos2unix {} \;

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
