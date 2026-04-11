FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir openenv-core fastapi uvicorn pydantic openai

# Copy source
COPY . .

# Install the package itself
RUN pip install --no-cache-dir -e .

EXPOSE 7860

# HF Spaces expects port 7860
CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "7860"]
