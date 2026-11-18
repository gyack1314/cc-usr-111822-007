FROM python:3.11-slim
WORKDIR /app
COPY . .
CMD ["python","-m","neuro_trial.cli","data/example.json"]
