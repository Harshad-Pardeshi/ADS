FROM dataquestio/python3-starter:latest
COPY adsassignment11.py /home/ds/adsassignment11.py 
COPY config.json /home/ds/config.json
WORKDIR /home/ds
USER ds
ENTRYPOINT ["/opt/ds/bin/python3", "/home/ds/adsassignment11.py"]