FROM python:3.11-slim

# Create a non-root user
# RUN useradd -m -u 1000 appuser

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Change ownership of the application files to appuser
# RUN chown -R appuser:appuser /app

# Switch to non-root user
# USER appuser

ENV PYTHONUNBUFFERED=1
EXPOSE 8082

CMD ["gunicorn", "--bind", "0.0.0.0:8081", "app:app"]