FROM debian:11-slim
ENV TZ=Europe/London
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
RUN apt-get update -y
RUN apt-get install -y python3-pip iputils-ping
COPY . /app
WORKDIR /app
RUN pip3 install -r requirements.txt
RUN pip3 install -r TasmotaCLI/requirements.txt
RUN pip3 install docker
ENTRYPOINT ["python3"]
CMD ["mqtt-client.py"]
