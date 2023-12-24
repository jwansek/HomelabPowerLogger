FROM ubuntu:20.04
ENV TZ=Europe/London
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
RUN apt-get update -y
RUN apt-get install -y python3-pip iputils-ping cron wget snmp snmp-mibs-downloader unzip
COPY . /app
WORKDIR /app
RUN wget "https://static.tp-link.com/upload/software/2022/202209/20220915/privateMibs(20220831).zip"
RUN mkdir -p /usr/share/snmp/mibs
RUN unzip -j "privateMibs(20220831).zip" -d  /usr/share/snmp/mibs
RUN pip3 install -r requirements.txt
RUN rm "privateMibs(20220831).zip"

RUN echo "*/1 * * * * root python3 /app/snmp-omada.py > /proc/1/fd/1 2>/proc/1/fd/2" > /etc/crontab
ENTRYPOINT ["bash"]
CMD ["entrypoint.sh"]