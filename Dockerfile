# AgentForge Docker Configuration
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# Create memory directory
RUN mkdir -p memory

# Expose port
EXPOSE 8000

# Run
CMD ["python", "api/main.py"]
