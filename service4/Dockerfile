FROM python:3.9-slim

WORKDIR /app

COPY service4.py /app/service4.py

RUN pip install flask flask_cors

EXPOSE 5003

CMD ["python", "service4.py"]
