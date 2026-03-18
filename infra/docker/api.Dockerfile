FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /workspace

COPY . .

RUN pip install --upgrade pip && \
    pip install -r services/api/requirements.txt

WORKDIR /workspace/services/api

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

