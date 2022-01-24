FROM python:3.10-slim-buster
WORKDIR /app/code
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY *.py ./
RUN apt-get update
RUN apt-get install iputils-ping sshpass -y
RUN echo "192.168.1.125		sokka.lionturtle.bried" >> /etc/hosts
CMD ["python3", "control.py"]
