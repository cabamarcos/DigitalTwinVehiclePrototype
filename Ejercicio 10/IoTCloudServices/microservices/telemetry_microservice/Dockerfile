FROM python:3.11.1

COPY ./code /etc/usr/src/app

WORKDIR /etc/usr/src/app

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "telemetry_manager_api.py"]
