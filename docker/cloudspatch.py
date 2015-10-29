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
CSP_CONF = "csp_conf"


class GitRepo:
    """A git repository"""

    def __init__(self, repo_or_config, isrepo=False, isconfig=False):
        self.path_on_disk = ""
        self.checkout_targets = []
        self.compress = None
        self.branch_for_write = ""
        self.ssl_key = ""
        self.ssl_key_dir = ""
        self.author_name = ""
        self.author_email = ""

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

    def run_clone_git(self):
        """Return path and a list of commands. Each command will be executed in
        the path"""

        command_list =\
            ["git config --global user.name \"" + self.author_name + "\"",
             "git config --global user.email \"" + self.author_email + "\"",
             "git config --global push.default simple"]

        return self.path_on_disk, command_list

    def run_config_git_env(self):
        """Return path and a list of commands. Each command will be executed in
        the path"""

        command_list =\
            ["git config --global user.name \"" + self.author_name + "\"",
             "git config --global user.email \"" + self.author_email + "\"",
             "git config --global push.default simple"]

        return self.path_on_disk, command_list

class Cocci:
    """A .cocci file"""

    def __init__(self, name, spatch_opts):
        self.name = name
        self.spatch_opts = spatch_opts

    def __run(self):
        """Return path and a list of commands. Each command will be executed in
        the path"""
        pass

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
        self.conf = None
        self.git_in = None
        self.git_out = None
        self.cocci_files = {}
        self.script_files = {}
        self.pipeline = None

        self.read_config()

    def is_config_ok(self):
        """ Check if the configuration looks ok"""

        # Is there a job_conf file?
        if len(self.conf) <= 2:
            print(self.no_config_message, file=sys.stderr)
            return False

        # Does the config file looks sane from far?
        problem = False
        for section in ["dir", "com", "git_in", "git_out", "cocci", "pipeline"]:
            if section not in self.conf.sections():
                print("Section " + section + " not found in the config file.",
                      file=sys.stderr)
                problem = True

        if problem:
            return False

        return True

    def read_config(self):
        """Read the job configuration file"""

        # Reading the configuration files
        self.conf = ConfigParser(interpolation=ExtendedInterpolation())
        self.conf.read([CSP_CONF, JOB_CONF])

        if not self.is_config_ok():
            print(JOB_CONF + " error. Exiting...", file=sys.stderr)
            exit(1)

        # [git_in]
        self.git_in = GitRepo(self.conf.get("git_in", "config_url"),
                              isconfig=True)
        self.git_in.set_checkout(self.conf.get("git_in", "checkout"))
        #self.git_in.set_checkout("      catapimba_peter    ")
        self.git_in.author_name = self.conf.get("com", "author")
        self.git_in.author_email = self.conf.get("com", "email")
        self.git_in.path_on_disk = self.conf.get("dir", "git_in_dir")

        # [git_out]
        self.git_out = GitRepo(self.conf.get("git_out", "repo_url"),
                               isrepo=True)
        self.git_out.set_compression()
        self.git_out.branch_for_write = self.conf.get("git_out", "branch")
        self.git_out.ssl_key = self.conf.get("git_out", "key")
        self.git_out.author_name = self.conf.get("com", "author")
        self.git_out.author_email = self.conf.get("com", "email")
        self.git_out.path_on_disk = self.conf.get("dir", "git_out_dir")

        # [cocci]
        cocci_def_opts = self.conf.get("cocci", "cocci_def_opts")

        job_cocci_files = self.conf.get("cocci", "cocci_files").split(",")
        self.cocci_files = {x: Cocci(x, cocci_def_opts) for x in
                            [x.strip() for x in job_cocci_files]}

        # [script]
        job_script_files = self.conf.get("script", "script_files").split(",")
        self.script_files = {x: Script(x) for x in
                             [x.strip() for x in job_script_files]}

        # [pipeline]
        self.pipeline = Pipeline(self.conf.get("pipeline", "pipeline"))

class ExecEnvironment:
    """ TheJob() has all important instances we will need during execution.
    Let's run it then."""

    def __init__(self, myjob):
        self.myjob = myjob
        self.exec_log = []
        self.outdir = ""
        self.indir = ""
        self.checkout_idx = 0
        self.pipeline_idx = 0

    def initialize(self):
        """Setup the execution environment"""
        self.indir = self.myjob.git_in.path_on_disk

        self.__run(self.myjob.git_out.run_setup())

        self.outdir = self.myjob.git_out.path_on_disk

    def pipeline(self):
        """Run the commands on the pipeline for each git_in.checkin_target"""

        for checkout in self.myjob.git_in.checkout_targets:
            for stage in self.myjob.pipeline.pipeline_stages:
                run_folder = self.myjob.git_out.get_pipe_run_dir(checkout,
                                                                 stage.name)
                ret_list = self.__run(stage.__run())
                if ret_list.count(0) != len(ret_list):
                    print("Something went wrong when running: " + stage.name +
                          ". Ignoring the error...", file=sys.stderr)

    def finalize(self):
        """Do this before exiting..."""
        pass

    def __run(self, path, command_list, log=True):
        """Run each command from command_list at path. The idea is that this is
        called only from initialize, pipeline, and finalize. log controls if the
        history of executed commands is saved at self.exec_log"""
        ret_list = []
        for command in command_list:
            self.exec_log.append(path + ":" + command)
            ret_list.append = call(command, shell=True, cwd=path)

        return ret_list



def main():
    """ Good old main """

    myjob = TheJob()

    print(myjob.git_in.config_url)
    print(myjob.git_in.checkout_targets)

    print(myjob.git_out.repo_url)
    print(myjob.git_out.compress)
    print(myjob.git_out.branch_for_write)
    #print(myjob.git_out.ssl_key)

    for cocci_file in myjob.cocci_files.keys():
        print(cocci_file)
    for script_file in myjob.script_files.keys():
        print(script_file)

    print(myjob.pipeline.pipeline_str)
    print(myjob.pipeline.stage_count)
    print(myjob.pipeline.pipeline_stages)

    print(myjob.git_in.author_name)
    print(myjob.git_out.author_name)

    print(myjob.git_in.path_on_disk)
    print(myjob.git_out.path_on_disk)
    print(myjob.git_out.configure_exec_env())

    return 0

if __name__ == '__main__':
    main()
