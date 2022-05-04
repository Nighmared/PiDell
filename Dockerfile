FROM python:3.10-slim-buster
WORKDIR /app/code
RUN apt-get update
RUN apt-get install iputils-ping sshpass lsb-release chromium-driver gcc libffi-dev -y
COPY requirements.txt requirements.txt
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
# act as if theres a display
ENV DISPLAY=:99


COPY *.py ./
RUN mkdir /root/.ssh
CMD ["python3", "control.py"]
