FROM debian:buster

RUN apt update && apt upgrade -y

RUN apt install mosquitto mosquitto-clients -y

RUN touch /etc/mosquitto/passwd

RUN mosquitto_passwd -b /etc/mosquitto/passwd fic_server fic_password

# COPY ./code/mosquitto.conf /etc/mosquitto/mosquitto.conf

CMD ["/usr/sbin/mosquitto", "-c", "/etc/mosquitto/mosquitto.conf"]
