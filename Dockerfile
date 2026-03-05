FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY hedera_shield/ hedera_shield/
COPY config/ config/

RUN mkdir -p logs

EXPOSE 8000

CMD ["uvicorn", "hedera_shield.api:app", "--host", "0.0.0.0", "--port", "8000"]
