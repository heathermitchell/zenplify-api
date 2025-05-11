# Use lightweight Python image
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Expose the app on port 5000
EXPOSE 5000

# Start with Gunicorn
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5000", "main:app"]
