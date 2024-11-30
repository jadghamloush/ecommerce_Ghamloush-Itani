FROM python:3.9-slim

WORKDIR /app

COPY service2.py /app/service2.py

RUN pip install flask flask_cors

EXPOSE 5001

CMD ["python", "service2.py"]
