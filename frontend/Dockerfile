# 1. Use a lightweight base image for cryptography/msal
FROM python:3.12-alpine

# 2. Install system dependencies needed for msal/cryptography
RUN apk add --no-cache gcc musl-dev libffi-dev curl

WORKDIR /app

# 3. Copy and install requirements
ARG REQUIREMENTS=requirements.txt
COPY frontend/requirements*.txt ./
RUN pip install --no-cache-dir -r $REQUIREMENTS

# 4. Copy Flask application files
# Build context is the repository root
COPY frontend/webapp/ webapp/

# 5. Set environment variables
ENV FLASK_APP=webapp/app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV PYTHONUNBUFFERED=1

EXPOSE 5000

# 6. Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# 7. Production Server with gunicorn
# Ensure your app object is named 'app' inside webapp/app.py
CMD ["gunicorn", "--workers=1", "--bind", "0.0.0.0:5000", "webapp.app:app"]
