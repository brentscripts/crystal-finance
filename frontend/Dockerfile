# 1. Use a slightly more robust base for cryptography/msal
FROM python:3.12-alpine

# 2. Install system dependencies needed for msal/cryptography
RUN apk add --no-cache gcc musl-dev libffi-dev

WORKDIR /app

# 3. Handle requirements
ARG REQUIREMENTS=requirements.txt
# Copy requirements from the root or frontend folder
COPY frontend/requirements*.txt ./
RUN pip install --no-cache-dir -r $REQUIREMENTS

# 4. Copy your Flask app files
# We use 'frontend/' prefix because the build context is the repository root
COPY frontend/webapp/ webapp/
COPY frontend/importers/ importers/
COPY frontend/main.py frontend/init_db.py frontend/schema.sql ./

# 5. Set environment variables
ENV FLASK_APP=webapp/app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV PYTHONUNBUFFERED=1

EXPOSE 5000

# 6. Production Server
# Ensure your app object is named 'app' inside webapp/app.py
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "webapp.app:app"]
