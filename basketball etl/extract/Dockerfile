FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY extract_games.py .

CMD ["python", "extract_games.py"]
