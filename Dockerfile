FROM python:3.14-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN apt-get update && apt-get install -y python3-tk tk-dev
COPY ./Python .
EXPOSE 6502/udp

CMD ["python", "WetherP.py"]
