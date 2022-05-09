FROM python:3.7-slim
WORKDIR /app/code
RUN mkdir -p /root/.ssh
# act as if theres a display
ENV DISPLAY=:99
RUN ln -s /usr/bin/dpkg-split /usr/sbin/dpkg-split
RUN ln -s /usr/bin/dpkg-deb /usr/sbin/dpkg-deb
RUN ln -s /bin/tar /usr/sbin/tar
RUN ln -s /bin/rm  /usr/sbin/rm
RUN apt-get update
RUN apt-get --fix-broken install -y
RUN apt-get --fix-broken install python3 -y
RUN apt-get install iputils-ping sshpass lsb-release chromium-driver -y
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt --extra-index-url https://piwheels.org/simple
COPY *.py ./
CMD ["python3", "control.py"]
