FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
COPY requirements.api.txt .
RUN python -m pip install -U pip && python -m pip install --only-binary=:all: -r requirements.api.txt
COPY services ./services
RUN mkdir -p /app/artifacts
EXPOSE 8000
CMD ["uvicorn", "services.poisson_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
