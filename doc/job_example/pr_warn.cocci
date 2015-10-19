@r1@
position p;
@@
pr_warn(...)@p

@script:python@
p << r1.p;
@@
print p[0].file, p[0].line

