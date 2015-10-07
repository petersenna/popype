# Based on the Fedora image
FROM petersenna/coccinelle-linux-git

RUN dnf -y install xz;dnf clean all

ADD ["cloudspatch.py", "/"]
ADD ["cloudspatch_conf", "/"]

ENTRYPOINT ["/cloudspatch.py"]
