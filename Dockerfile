FROM python:3.10-slim-buster
WORKDIR /app/code
RUN apt-get update
RUN apt-get install iputils-ping sshpass lsb-release chromium-driver -y
RUN apt-get install gcc libffi-dev -y
COPY requirements.txt requirements.txt
COPY *.py .
RUN pip install -r requirements.txt --extra-index-url https://piwheels.org/simple
# act as if theres a display
ENV DISPLAY=:99
RUN mkdir /root/.ssh
CMD ["python3", "control.py"]
