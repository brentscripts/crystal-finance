# Use official Python image

FROM python:3.13.7-alpine3.21

WORKDIR /app

# Allow switching requirements file via build arg
ARG REQUIREMENTS=requirements.txt
COPY requirements.txt requirements-dev.txt ./

# Select requirements file via build arg (default: requirements.txt)
ARG REQUIREMENTS=requirements.txt
RUN pip install --no-cache-dir -r $REQUIREMENTS

# Copy only necessary files
COPY webapp/ webapp/
COPY database/ database/
COPY importers/ importers/
COPY main.py init_db.py schema.sql ./
COPY webapp/templates/ webapp/templates/
COPY webapp/static/ webapp/static/

# Set environment variables
ENV FLASK_APP=webapp/app.py
ENV FLASK_ENV=production

EXPOSE 5000

# Use Gunicorn for production
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "webapp.app:app"]
