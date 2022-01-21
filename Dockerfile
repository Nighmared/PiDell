FROM python:latest
WORKDIR /app/code
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
COPY *.py ./
RUN apt-get update
RUN apt-get install iputils-ping -y
CMD ["python3", "control.py"]