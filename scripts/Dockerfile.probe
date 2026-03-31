FROM python:3.11-slim
RUN pip install google-cloud-aiplatform google-auth
WORKDIR /app
COPY probe_models.py .
CMD ["python", "probe_models.py"]
