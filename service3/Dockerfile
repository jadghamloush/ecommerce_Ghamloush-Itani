FROM python:3.9-slim

WORKDIR /app

COPY service3.py /app/service3.py

RUN pip install flask flask_cors

EXPOSE 5002

CMD ["python", "service3.py"]
