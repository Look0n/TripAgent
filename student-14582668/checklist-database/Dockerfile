FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app.py schema.sql init.sql ./

RUN mkdir -p /data

ENV DATABASE_PATH=/data/checklist.db
ENV CHECKLIST_DATABASE_PORT=6004

EXPOSE 6004

CMD ["python", "app.py"]
