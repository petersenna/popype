# Based on the Fedora image
FROM petersenna/coccinelle-linux-git

RUN dnf -y install xz;dnf clean all

ADD ["cloudspatch.py", "/"]
ADD ["csp_conf", "/"]
ADD ["job_conf", "/"]

ENTRYPOINT ["/cloudspatch.py"]
