FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app.py schema.sql init.sql ./

RUN mkdir -p /data

ENV DATABASE_PATH=/data/checklist.db
ENV CHECKLIST_DATABASE_PORT=6005

EXPOSE 6005

CMD ["python", "app.py"]
