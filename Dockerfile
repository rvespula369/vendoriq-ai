FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml ./
RUN pip install --no-cache-dir .
COPY src ./src
COPY app.py ./app.py
ENV PYTHONPATH=/app/src
EXPOSE 7860
CMD ["python", "app.py"]
