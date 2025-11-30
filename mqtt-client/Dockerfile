FROM debian:12-slim
ENV TZ=Europe/London
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
RUN apt-get update -y
RUN apt-get install -y python3-pip iputils-ping
COPY . /app
WORKDIR /app
RUN pip3 install --break-system-packages -r requirements.txt
RUN pip3 install --break-system-packages docker
RUN pip3 install --break-system-packages -r TasmotaCLI/requirements.txt 
ENTRYPOINT ["python3"]
CMD ["mqtt-client.py"]
