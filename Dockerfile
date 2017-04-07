FROM python:3

USER root

ADD Luigi_Test.py Luigi_Test.py

RUN apt-get update && \
    apt-get clean && \
        rm -rf /var/lib/apt/lists/*

	USER $NB_USER
    
    # Install Python 3 packages
	# Remove pyqt and qt pulled in for matplotlib since we're only ever going to
	# use notebook-friendly backends in these images
	RUN pip install boto
	RUN pip install luigi
	#RUN pip install urllib3
	#RUN	pip install bs4
	#RUN pip install requests
	#RUN pip install numpy
	#RUN pip install pandas
	#RUN	pip install lxml
	#RUN	pip install sklearn
	#RUN	pip install scipy
	#RUN	pip install https://github.com/pybrain/pybrain/archive/0.3.3.zip

#RUN pip install pystrich

CMD [ "python", "./Luigi_Test.py", "UploadToS3", "--local-scheduler", "--awsKey", "<Access Key>", "--awsSecret", "<Secret key>" ]