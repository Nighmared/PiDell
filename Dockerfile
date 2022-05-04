FROM python:3.10-slim-buster
WORKDIR /app/code
RUN apt-get update
RUN apt-get install iputils-ping sshpass lsb-release wget curl unzip -y
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
RUN wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
RUN apt-get install ./google-chrome-stable_current_amd64.deb -y
RUN wget -O /tmp/chromedriver.zip http://chromedriver.storage.googleapis.com/`curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE`/chromedriver_linux64.zip
RUN unzip /tmp/chromedriver.zip chromedriver -d /usr/local/bin/
# act as if theres a display
ENV DISPLAY=:99


COPY *.py ./
RUN mkdir /root/.ssh
CMD ["python3", "control.py"]
