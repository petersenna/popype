# Based on the Fedora image
FROM petersenna/coccinelle-linux-git

RUN dnf -y install xz;dnf clean all

RUN mkdir -p /usr/local/cloudspatch
ADD ["cloudspatch.py", "/usr/local/cloudspatch/"]
ADD ["cloudspatch_conf", "/usr/local/cloudspatch/"]

ENTRYPOINT ["/usr/local/cloudspatch/cloudspatch.py"]
