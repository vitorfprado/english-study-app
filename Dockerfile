FROM python:3.12-slim AS base

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN pip install --no-cache-dir --upgrade pip

COPY requirements/base.txt ./requirements/base.txt
RUN pip install --no-cache-dir -r requirements/base.txt

COPY alembic.ini .
COPY alembic ./alembic
COPY app ./app

RUN mkdir -p uploads/materials

FROM base AS web
COPY requirements/web.txt ./requirements/web.txt
RUN pip install --no-cache-dir -r requirements/web.txt
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM base AS worker-pdf
COPY requirements/worker-pdf.txt ./requirements/worker-pdf.txt
RUN pip install --no-cache-dir -r requirements/worker-pdf.txt
CMD ["python", "-m", "app.workers.pdf_worker"]

FROM base AS worker-ai
COPY requirements/worker-ai.txt ./requirements/worker-ai.txt
RUN pip install --no-cache-dir -r requirements/worker-ai.txt
CMD ["python", "-m", "app.workers.ai_worker"]
