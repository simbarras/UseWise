FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .
COPY usewise/ usewise/

RUN pip install --no-cache-dir -e .

# Default DB path; override with DB_PATH env var (mount a volume here)
ENV DB_PATH=/data/usewise_feedback.db

EXPOSE 8000

CMD ["uvicorn", "usewise.restApi.router:app", \
     "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
