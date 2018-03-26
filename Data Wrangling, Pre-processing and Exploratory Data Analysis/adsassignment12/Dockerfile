FROM dataquestio/python3-starter:latest
COPY adsassignment12.py /home/ds/adsassignment12.py 
COPY config.json /home/ds/config.json
WORKDIR /home/ds
USER ds
ENTRYPOINT ["/opt/ds/bin/python3", "/home/ds/adsassignment12.py"]