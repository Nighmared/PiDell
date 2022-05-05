FROM python:3.7-slim
WORKDIR /app/code
RUN ln -s /usr/bin/dpkg-split /usr/sbin/dpkg-split
RUN ln -s /usr/bin/dpkg-deb /usr/sbin/dpkg-deb
RUN apt-get update
RUN apt-get install iputils-ping sshpass lsb-release chromium-driver -y
COPY requirements.txt requirements.txt
COPY *.py .
RUN pip install -r requirements.txt --extra-index-url https://piwheels.org/simple
# act as if theres a display
ENV DISPLAY=:99
RUN mkdir /root/.ssh
CMD ["python3", "control.py"]
