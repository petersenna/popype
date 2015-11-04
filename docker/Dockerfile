# Based on the Fedora image
FROM petersenna/coccinelle-linux-git

RUN dnf -y install xz;dnf clean all

ADD ["spatch-wrapper", "/usr/local/bin"]
ADD ["popype.py", "/"]
ADD ["popype_conf", "/"]
ADD ["job_conf", "/"]

ENTRYPOINT ["/popype.py"]
