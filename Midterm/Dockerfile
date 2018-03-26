# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.
FROM jupyter/minimal

MAINTAINER Jupyter Project <kamath.p@husky.neu.edu>

USER root


ADD adsmidtermpart1.py adsmidtermpart1.py
ADD config.json config.json

# WORKDIR /srv/
EXPOSE 8888
CMD ["bash"]

#-c 'jupyter notebook --ip=8888 --NotebookApp.password="$PASSWD" "$@"'