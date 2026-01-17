FROM python:3.11-slim

WORKDIR /code

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Environment variables will be overridden by docker-compose
ENV TEMPORAL_HOST=localhost:7233

CMD ["python", "app/main.py"]
