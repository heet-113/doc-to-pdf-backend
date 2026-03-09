# Use a slim Debian-based Python image
FROM python:3.11-slim

# Install LibreOffice — this is what does the actual DOCX/CSV → PDF conversion.
# It perfectly preserves fonts, layouts, tables, and all formatting.
RUN apt-get update && \
    apt-get install -y --no-install-recommends libreoffice && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

# Expose port (Render injects $PORT at runtime)
EXPOSE 5000

# Use gunicorn for production; timeout=120 to allow longer conversions
CMD gunicorn --bind 0.0.0.0:${PORT:-5000} --timeout 120 app:app
