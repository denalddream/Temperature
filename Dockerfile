FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    iproute2 \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir requests

COPY WetherP.py .

EXPOSE 6502/udp

CMD ["python", "WetherP.py"]
