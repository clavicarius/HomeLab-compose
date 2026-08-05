FROM python:3.13-alpine

WORKDIR /app
COPY server.py .
COPY static ./static

EXPOSE 8080
CMD ["python", "server.py"]