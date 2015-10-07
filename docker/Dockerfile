# Based on the Fedora image
FROM petersenna/coccinelle-linux-git

RUN mkdir -p /usr/local/cloudspatch
ADD ["cloudspatch.py", "/usr/local/cloudspatch/"]
ADD ["cloudspatch_conf", "/usr/local/cloudspatch/"]

ENTRYPOINT ["/usr/local/cloudspatch.py"]
