FROM python:3.11.1

COPY ./code /etc/usr/src/code

WORKDIR /etc/usr/src/code

RUN pip install --no-cache-dir -r requirements.txt

ENTRYPOINT ["python"]

CMD ["VehicleDigitalTwin.py"]
