#!/usr/bin/env python3
""" Cloudspatch allows you to specify a pipeline of Coccinelle semantic patches
and scripts to create code analysis and code transformation tools. It expects a
git repositories to read code from, e.g. the Linux kernel, and it expects a git
repository to write to. The pipeline and the git details are defined in
configuration file. This is under development, and sensitive readers should not
read after this point."""

__author__ = "Peter Senna Tschudin"
__email__ = "peter.senna@gmail.com"
__license__ = "GPLv2"
__version__ = "Alpha 2"

#from configparser import ConfigParser, ExtendedInterpolation, NoOptionError
#from subprocess import call, check_output, Popen, PIPE
#import os, filecmp, shutil
from configparser import ConfigParser, ExtendedInterpolation
import os

class GitRepo:
    """A git repository"""

    def __init__(self, repo_or_config, isrepo=False, isconfig=False):
        self.checkout_targets = []
        self.compress = None
        self.branch_for_write = ""
        self.ssl_key = ""

        if isrepo:
            self.repo_url = repo_or_config

        if isconfig:
            self.config_url = repo_or_config

    def set_checkout(self, checkout_csv):
        """Define the checkout targets"""
        self.checkout_targets = [x.strip() for x in checkout_csv.split(",")]

    def set_compression(self):
        """Should stdout and stderr be compressed before committing?"""
        self.compress = True

    def set_branch(self, branch):
        """Define the branch to use when writing to git"""
        self.branch_for_write = branch

    def set_ssl_key(self, key):
        """Define the ssl key of your git repository when needed"""
        self.ssl_key = key

class Cocci:
    """A .cocci file"""

    def __init__(self, name, spatch_opts):
        self.name = name
        self.spatch_opts = spatch_opts

class Script:
    """A script"""

    def __init__(self, name):
        self.name = name

class Pipeline:
    """This is not like a pipe from Bash. Instead of doing stdout to stdin magic
    using real, and in memory pipes, stdout and stderr are saved to disk, and
    then full path to these files are passed around."""

    def __init__(self, pipeline_str):
        self.pipeline_stages = []
        self.stage_count = 0

        self.pipeline_str = pipeline_str
        self.parse_pipeline()

    def parse_pipeline(self):
        """Transform the string from the user to a list"""
        self.pipeline_stages = [x.strip() for x in self.pipeline_str.split("|")]

        self.stage_count = len(self.pipeline_stages)

class TheJob:
    """Store the instances related to the job described on the job_conf file"""

    def __init__(self):
        self.job_conf = None
        self.git_in = None
        self.git_out = None
        self.cocci_def_opts = ""
        self.cocci_files = {}
        self.script_files = {}
        self.pipeline = None

        self.read_config()

    def read_config(self):
        """Read the job configuration file"""

        # Reading the configuration file
        # This is the configuration file describing an specific job.
        self.job_conf = ConfigParser(interpolation=ExtendedInterpolation())
        self.job_conf.read("job_conf")

        # [git_in]
        self.git_in = GitRepo(self.job_conf.get("git_in", "config_url"),
                              isconfig=True)
        self.git_in.set_checkout(self.job_conf.get("git_in", "checkout"))
        #self.git_in.set_checkout("      catapimba_peter    ")

        # [git_out]
        self.git_out = GitRepo(self.job_conf.get("git_out", "repo_url"),
                               isrepo=True)
        self.git_out.set_compression()
        self.git_out.set_branch(self.job_conf.get("git_out", "branch"))
        self.git_out.set_ssl_key(self.job_conf.get("git_out", "key"))

        # [cocci]
        self.cocci_def_opts = self.job_conf.get("cocci", "cocci_def_opts")

        job_cocci_files = self.job_conf.get("cocci", "cocci_files").split(",")

        self.cocci_files = {x: Cocci(x, self.cocci_def_opts) for x in
                            [x.strip() for x in job_cocci_files]}

        # [script]
        jc_script_files = self.job_conf.get("script", "script_files")
        for script_file in jc_script_files.split(","):
            script_file = script_file.strip()
            self.script_files[script_file] = Script(script_file)

        # [pipeline]
        self.pipeline = Pipeline(self.job_conf.get("pipeline", "pipeline"))

#class Cocci:
#    """.cocci file on the pipeline"""
#    def __init__(self):
#
#class Script:
#    """script on the pipeline"""
#    def __init__(self):
#
#class Pipeline:
#    """An example pipeline:
#
#          step1.cocci|finalize1.py|step2.cocci|post.py
#
#          *.cocci apply the semantic patch on each checkout of linus.git
#          *.py apply the script to stdout of previous semantic patch
#             it will create one directory with the branch name: branch
#                one directory for each checkout: v4.2
#                   one directory for each stage of the pipeline: step1,
#                   finalize1, step2, post
#            branch/v4.2/{step1, finalize1, step2, post}
#    Will also print the last stdout of the pipeline before exiting"""
#
#    def __init__(self):
#        git_in = GitRepo()
#        git_out = GitRepo()
#        cocci_scripts = Cocci()
#        scripts = Script()


#def utopic_test():
#
#    pl = Pipeline()
#
#    # Pipeline.GitRepo accept an URL to a git config file
#    pl.git_in = Pipeline.GitRepo("http://github.com/petersenna/cocci-linux-git/config")
#    pl.git_in.checkout = """v2.6.12, v2.6.15, v2.6.20, v2.6.25, v2.6.30,
#            v2.6.35, v3.0, v3.10, v3.15, v3.5, v4.0, v4.2"""
#    # This would be nice!
#    pl.git_in.checkout_regex = "^v2\.6\.[0-9]*$|^v[34]\.[0-9]*$"
#
#    # Pipeline.GitRepo accept an URL to a git repository
#    pl.git_out = Pipeline.GitRepo("git@github.com:petersenna/fake.git")
#    pl.git_out.ssh_key = """-----BEGIN RSA PRIVATE KEY-----
#            MIIEpAIBAAKCAQEA7SQQS+WTFO67OgZ1PGMo2fUtc81K2x/7gbz3Ln30bOuCbFLm
#            +/oqToouhhLdd0o9Oe9JZ7m39LcIjl7tbZEQ2QxAHk/946vhrwUVBNX+fq6mwAGP
#            GcU3FEjL7JirAjv6rd61VHx/hxUFEdt+MZ57lxPKONRG8RxB43Uh2TtXxvSXrkLe
#            8DXY5nTAQHHPaR6U0FsfzuhKSXE7OpXk4OqnbI14CCRsnav7XoB8XY2E7y5ju/Er
#            MMoL7G5MSN4CgGQ71XFHmCNzOgw3dlEzxWOgLmYpy7iY/4PpYbtdpHMEAPqPz6YW
#            cskSqg2GAoKY9XePPHNz2jNsFSB3riT/jQBFowIDAQABAoIBABc4LcRQsUseaQSw
#            dzA3gVt+DzpEgqzb/9NfPlC2EoXLtZSHtYg8oYHZM9763+Z7RW1zyZs3axSyC0tt
#            bhAJYT3vXiPZr0FopgtuEvXLQkUDMt6gCHP8hH0e96Ct/iiU2OHHabfhDNecLkfm
#            Vv/ixbUwQd+4oU2gd68e2/aaQej//8kgqA0zVqxktXtDRcAWrrOnJ4x52mo+VoKi
#            AEkgy5vwtC0tPqc9/GceKO2Brtudv7Q3B6JvTe8rlMHr9lUrHh7LINuWDiGlNx5T
#            S+3YmlLtBTdk2Fir33KPGb3y99pfrCVFyBJhntBpW4HeMMrRYr88nJqSSP303HiS
#            /ddMkJECgYEA/U8AC6ZqjvUqi1N2v9I0wQmUT6h6LpDX6dGBrseUzs5Vj2+WTWmH
#            Wqooe/JuRtKfFyWpwepchjeaPcA/n8HoujkRWtiXSF8b4uqTJCgkGlDfN3WtRwKZ
#            9Zq+euB3iLhEOXtE93mpL7d4EfrX/6Yhc+9SYYHOsuYEinf3jBJUwGsCgYEA76kW
#            VhtDGHwQ4k5paEJwwdnFm7RG+gG8CR+nTcp2K7pUyYXynyoQdJ4PePOdc+qrA0Nj
#            yCobAbfMwlDl3ZzLPjGHUGo3uRbivF5Tktwjyi7HDPgC8+/mUTEfvb3uFcesit9L
#            FfNaKfUria70Qb3+y8SEiKnmwWR+P5NPyIWLfakCgYEA8kz8LSitqzumy4k2APzx
#            C2m/XYc6AIr6jaWjF+2/UScbvs2thzUXjUlQ2mcmx0Y3eavEO0KT6KsNNl5MPeP9
#            Wwy1piGibE7V3PQndaGUDzwmmOVOr6s0XDP+WomWrcgdMqLQcK0GgidMil5Y+SkP
#            vNdDBRRnBMdztoRU3b63JSsCgYByXmOtZccoKRS5mqfMvGAo8i7ONkLkze0ZAYUK
#            p4KrLXmGzihRcnZ14HQLyV4rUiKYJRG6FPXcZQUO+iIoFsoa/PHRG09KQbSkJfOG
#            Ew31T0toUfa+yI5F0saN+tRiim45u4OOjxpJCZnkU5x2vx+XyEljGolnYvioiDk7
#            vRcrOQKBgQCxaX/FDHoWL6ZMf+CqBwN7Sr0n2JXkVVQjpp7LZ2TQiB3L3TSoIAK4
#            k9Wujr1dD5J0jZZy4/wIE9E/yVOF+EvizaOLiFaqXtgmAEXq9k9Cbq1V1z/IGMm+
#            fMvZmIy+WPp/77d24/iCwnljKJ4XTNR25Bl8H8NKhTvaIIhlznrrcA==
#            -----END RSA PRIVATE KEY-----"""
#    pl.git_out.branch = "test-20151016"
#    pl.git_out.author = "Peter Senna Tschudin"
#    pl.git_out.email = "peter.senna@gmail.com"
#
#    # Pipeline.Cocci accept a file name or URL
#    pl.log_in_if_cocci = Pipeline.Cocci("log_in_if.cocci")
#    pl.log_in_if_cocci.opts = "--timeout 120"
#    pl.log_in_if_cocci.compress = True
#    pl.log_in_if_cocci.parallel = True
#
#    # Pipeline.Cocci accept a file name or URL
#    pl.log_num_args_cocci = Pipeline.Cocci("log_num_args.cocci")
#    pl.log_num_args_cocci.opts = "--timeout 120"
#    pl.log_num_args_cocci.compress = True
#    pl.log_num_args_cocci.parallel = True
#
#    # Pipeline.Cocci accept a file name or URL
#    pl.log_f_call_cocci = Pipeline.Cocci("log_f_call.cocci")
#    pl.log_f_call_cocci.opts = "--timeout 120"
#    pl.log_f_call_cocci.compress = True
#    pl.log_f_call_cocci.parallel = True
#
#    # Pipeline.Script accept a file name or URL
#    pl.filter_by_num_args_sc = Pipeline.Script("filter_by_num_args.py")
#    pl.filter_by_num_args_sc.compress = "gz"
#
#    # Pipeline.Script accept a file name or URL
#    pl.count_f_calls_sc = Pipeline.Script("count_f_calls.py")
#    pl.count_f_calls_sc.compress = "gz"
#
#    pl.run("""git_in: log_in_if_cocci | log_num_args_cocci |
#            filter_by_num_args_sc | log_f_call_cocci |
#            count_f_calls_sc > git_out""")
#

def main():
    """ Good old main """
    # This is configuration file for cloudspatch, with settings that
    # apply to all jobs
    csp_conf = ConfigParser(interpolation=ExtendedInterpolation())
    csp_conf.read("cloudspatch_conf")

    # Is there a job_conf file?
    if not os.path.exists("job_conf"):
        print("This is not suposed to do anything, you should specify a job.")
        print("Create a job_conf file and create a new container FROM this one")
        print("Example job_conf:")
        print("  github.com/petersenna/cloudspatch/tree/master/doc/job_example")
        exit(1)

    myjob = TheJob()

    print(myjob.git_in.config_url)
    print(myjob.git_in.checkout_targets)

    print(myjob.git_out.repo_url)
    print(myjob.git_out.compress)
    print(myjob.git_out.branch_for_write)
    #print(myjob.git_out.ssl_key)

    print(myjob.cocci_def_opts)
    for cocci_file in myjob.cocci_files.keys():
        print(cocci_file)
    for script_file in myjob.script_files.keys():
        print(script_file)

    print(myjob.pipeline.pipeline_str)
    print(myjob.pipeline.stage_count)
    print(myjob.pipeline.pipeline_stages)

    return 0

if __name__ == '__main__':
    main()
