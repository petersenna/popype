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
import sys

# Some ugly globals for configuration file names
JOB_CONF = "job_conf"
CSP_CONF = "cloudspatch_conf"

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

    no_config_message = (
        "This is not suposed to do anything, you should specify a job.\n"
        "Create a " + JOB_CONF + " file and create a new container FROM\n"
        "this one. Example " + JOB_CONF + ":\n"
        "\n"
        "    github.com/petersenna/cloudspatch/tree/master/Doc/job_example\n")

    def __init__(self):
        self.job_conf = None
        self.git_in = None
        self.git_out = None
        self.cocci_def_opts = ""
        self.cocci_files = {}
        self.script_files = {}
        self.pipeline = None

        self.read_config()

    def is_config_ok(self):
        """ Check if the configuration looks ok"""

        # Is there a job_conf file?
        if len(self.job_conf) <= 1:
            print(self.no_config_message, file=sys.stderr)
            return False

        # Does the config file looks sane from far?
        problem = False
        for section in ["com", "git_in", "git_out", "cocci", "pipeline"]:
            if section not in self.job_conf.sections():
                print("Section " + section + " not found in the config file.",
                      file=sys.stderr)
                problem = True

        if problem:
            return False

        return True

    def read_config(self):
        """Read the job configuration file"""

        # Reading the configuration file
        # This is the configuration file describing an specific job.
        self.job_conf = ConfigParser(interpolation=ExtendedInterpolation())
        self.job_conf.read(JOB_CONF)

        if not self.is_config_ok():
            print(JOB_CONF + " error. Exiting...", file=sys.stderr)
            exit(1)

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
        job_script_files = self.job_conf.get("script",
                                             "script_files").split(",")
        self.script_files = {x: Script(x) for x in
                             [x.strip() for x in job_script_files]}

        # [pipeline]
        self.pipeline = Pipeline(self.job_conf.get("pipeline", "pipeline"))

class CloudSpatch:
    """This class holds global configuration of CloudSpatch"""
    def __init__(self):
        self.cspatch_conf = ConfigParser(interpolation=ExtendedInterpolation())
        self.cspatch_conf.read(CSP_CONF)

def main():
    """ Good old main """
    # This is configuration file for cloudspatch, with settings that
    # apply to all jobs
    mycspatch = CloudSpatch()

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
