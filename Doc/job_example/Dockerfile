FROM petersenna/cloudspatch
ADD ["job_conf", "/"]

# You can comment this line if you specify a base url for downloading
# the .cocci files
ADD ["*.cocci", "/tmp/"]

ENTRYPOINT ["/cloudspatch.py"]
