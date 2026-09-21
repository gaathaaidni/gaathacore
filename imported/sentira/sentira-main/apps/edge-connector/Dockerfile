FROM python:3.12-slim

RUN useradd --create-home --uid 10001 sentira
WORKDIR /opt/sentira-edge
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY --chown=sentira:sentira . .
USER sentira
CMD ["python", "main.py"]
