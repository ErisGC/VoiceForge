FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /workspace

COPY . .

RUN pip install --upgrade pip && \
    pip install -r services/worker/requirements.txt

WORKDIR /workspace/services/worker

CMD ["python", "worker.py"]

