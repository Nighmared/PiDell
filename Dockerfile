FROM python:3.10-slim-buster
WORKDIR /app/code
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
COPY *.py ./
RUN apt-get update
RUN apt-get install iputils-ping sshpass -y
RUN mkdir /root/.ssh
CMD ["python3", "control.py"]
