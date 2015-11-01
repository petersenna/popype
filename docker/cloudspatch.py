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

from configparser import ConfigParser, ExtendedInterpolation
import filecmp, os, shutil, sys, subprocess, time

# Some ugly globals for names of configuration files
CSP_CONF = "csp_conf"
JOB_CONF = "job_conf"

class GitRepoConfig:
    """Configuration of the Git repository, mostly from the configuration
    files"""

    def __init__(self, repo_or_config, isrepo=False, isconfig=False):
        self.author_email = ""
        self.author_name = ""
        self.branch_for_write = ""
        self.checkout_targets = []
        self.compress = None
        self.repo_dir = ""
        self.ssl_key = ""
        self.ssl_key_path = ""

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

class GitRepoState:
    """ State of the repository, e.g.: Is it initialized? Is it checked out? To
    which checkout target? """

    def __init__(self, conf, exec_env):
        self.changes_to_commit = False
        self.checkout_idx = None
        self.conf = conf
        self.exec_env = exec_env
        self.initialized = False
        self.run = self.exec_env.run

    def reset_clean(self):
        """git reset --hard; git clean -f -x -d"""

        self.git_reset("--hard")
        self.git_clean("-f -x -d")

    def git_branch(self, opts, iscritical=False):
        """Guess what: git branch opts"""

        self.run(self.conf.repo_dir, "git branch " + opts, iscritical)

    def git_checkout(self, opts, iscritical=False):
        """Guess what: git checkout opts"""
        # git reset --hard; git clean -f -x -d; git checkout ...
        #call("git reset --hard", shell=True, cwd=linux_dir)
        #call("git clean -f -x -d", shell=True, cwd=linux_dir)
        #ret = call("git checkout " + checkout, shell=True, cwd=linux_dir)
        #if ret != 0:
        #    print("Could not checkout. Something is wrong...")
        #    return -1

        self.run(self.conf.repo_dir, "git checkout " + opts, iscritical)

    def git_clean(self, opts):
        """Guess what: git clean"""

        self.run(self.conf.repo_dir, "git clean " + opts)

    def git_clone(self):
        """Guess what: git clone"""

        self.run(self.conf.repo_dir, "git clone " + self.conf.repo_url + " .",
                 iscritical=True)

    def git_config(self, opts):
        """Guess what: git config opts"""

        self.run(self.conf.repo_dir, "git config " + opts, iscritical=True)

    def git_init(self):
        """Guess what: do a git init"""

        self.run(self.conf.repo_dir, "git init", iscritical=True)

    def git_push(self, opts, iscritical=False):
        """Guess what: git push opts"""

        self.run(self.conf.repo_dir, "git push " + opts, iscritical)

    def git_remote_update(self):
        """Guess what: do a git remote update"""

        self.run(self.conf.repo_dir, "git remote update", iscritical=True)

    def git_reset(self, opts):
        """Guess what: git reset"""

        self.run(self.conf.repo_dir, "git reset " + opts)

    def isbranch(self, branch):
        """Return true if branch exist, False if not"""

        git_cmd = "git branch -a"
        branches = self.exec_env.check_output(self.conf.repo_dir, git_cmd)
        if branch in branches:
            return True

        return False

    def init(self):
        """Run all initialization procedures"""

        # Some global configurations
        self.git_config("--global user.name \"" + self.conf.author_name + "\"")
        self.git_config("--global user.email \"" +
                        self.conf.author_email + "\"")
        self.git_config("--global push.default simple")

        # Repository can be defined by an url to a git config file or by an url
        # to use in git clone
        try:
            self.conf.repo_url
        except NameError:
            self.init_by_config()
        else:
            self.init_by_url()

    def init_by_config(self):
        """Init a git repository from on a config file, aka .git/config. The
        hacky detail: This is made for the git_in repository, the repository
        providing the source code for analysis."""

        repo_path = self.conf.repo_dir
        config_file_path = repo_path + "/.git/config"

        # Download the config file. Abort the entire execution if it fails
        dl_config_file_path = self.exec_env.download(self.conf.config_url,
                                                     "config", iscritical=True)
        # The git_in repo is probably already there
        # Is there a git config file there?
        if os.path.exists(config_file_path):
            # Yes!
            if filecmp.cmp(dl_config_file_path, config_file_path):
                # Cool the two config files are the same
                self.git_remote_update()
                return

        # If we got here it means that or the config file is not there or it is
        # different. Best to do is to delete everything and start a new
        # repository
        self.exec_env.rmtree(repo_path, iscritical=True)

        # Create /path/to/repo/.git
        self.exec_env.makedirs(os.path.dirname(config_file_path),
                               iscritical=True)

        # Copy the config file
        self.exec_env.copy(dl_config_file_path, config_file_path,
                           iscritical=True)

        self.git_init()
        self.git_remote_update()

    def init_by_url(self):
        """Init a git repository from an url e.g. git clone url. The hacky
        detail: This is made for the git_out repository, the repository to which
        cloudspatch will write to."""

        repo_url = self.conf.repo_url
        repo_dir = self.conf.repo_dir
        key_path = self.conf.ssl_key_path
        branch = self.conf.branch_for_write

        # Create ~/.ssh for id_rsa
        key_dir = os.path.dirname(key_path)
        self.exec_env.makedirs(key_dir)

        # Save the id_rsa aka private key
        # Why create a file at /tmp and then copy it to the destination folder?
        # To have a log of what is going on. There isn't a method to create a
        # file at exec_env
        self.exec_env.create_file(self.conf.ssl_key, key_path)

        # Fix private key permissions
        self.exec_env.chmod("0600 " + key_path)

        # This adds one entry to ~/.ssh/known_hosts
        self.exec_env.ssh_handshake(repo_url)

        # This directory should not exist, delete it and create again
        self.exec_env.rmtree(repo_dir)
        self.exec_env.makedirs(repo_dir)

        # Finally clone the directory
        self.git_clone()

        # Our branch: check if it exists, if not create it
        # Also create the directory tree and copy the cocci file
        if self.isbranch(branch):
            self.git_checkout("remotes/origin/" + branch, iscritical=True)
            self.git_checkout("-b " + branch, iscritical=True)
        else:
            self.git_checkout("-b " + branch, iscritical=True)
            self.git_push("origin " + branch, iscritical=True)

        # Track the remote branch
        self.git_branch("-u origin/" + branch, iscritical=True)

        self.git_push("--dry-run", iscritical=True)

class GitRepo:
    """A git repository"""
    def __init__(self, repo_or_config, isrepo=False, isconfig=False):
        self.conf = GitRepoConfig(repo_or_config, isrepo, isconfig)
        self.state = None

    def set_state(self, exec_env):
        """When an instance of GitRepo is created it is likely that there is no
        execution state available. This is used to set the state given an
        instance of ExecEnv()"""
        self.state = GitRepoState(self.conf, exec_env)

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

class JobConfig:
    """Store the instances related to the job described on the job_conf file"""

    no_config_message = (
        "This is not suposed to do anything, you should specify a job.\n"
        "Create a " + JOB_CONF + " file and create a new container FROM\n"
        "this one. Example " + JOB_CONF + ":\n"
        "\n"
        "    github.com/petersenna/cloudspatch/tree/master/Doc/job_example\n")

    def __init__(self, exec_env):
        self.cocci_files = {}
        self.conf = None
        self.exec_env = exec_env
        self.git_in = None
        self.git_out = None
        self.pipeline = None
        self.script_files = {}

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
        self.git_in.conf.set_checkout(self.conf.get("git_in", "checkout"))
        #self.git_in.set_checkout("      catapimba_peter    ")
        self.git_in.conf.author_name = self.conf.get("com", "author")
        self.git_in.conf.author_email = self.conf.get("com", "email")
        self.git_in.conf.repo_dir = self.conf.get("dir", "git_in_dir")
        self.git_in.set_state(self.exec_env)

        # [git_out]
        self.git_out = GitRepo(self.conf.get("git_out", "repo_url"),
                               isrepo=True)
        self.git_out.conf.set_compression()
        self.git_out.conf.branch_for_write = self.conf.get("git_out", "branch")
        self.git_out.conf.ssl_key = self.conf.get("git_out", "key")
        self.git_out.conf.ssl_key_path = self.conf.get("dir", "ssl_key_dir")
        self.git_out.conf.ssl_key_path += "/id_rsa"
        self.git_out.conf.author_name = self.conf.get("com", "author")
        self.git_out.conf.author_email = self.conf.get("com", "email")
        self.git_out.conf.repo_dir = self.conf.get("dir", "git_out_dir")
        self.git_out.set_state(self.exec_env)

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

class Logger:
    """This class does logging!"""

    def __init__(self, enable_log):
        self.enable_log = enable_log
        self.exec_log = []

    def log(self, cwd, command, ret=""):
        """Log the execution to a list"""
        if self.enable_log:
            secs = str(time.time()).split(".")[0]
            log_str = secs + "$ cd " + cwd + "; " + str(command)
            if ret:
                log_str += " ($? = " + str(ret) + ")"

            self.exec_log.append(log_str)

    def print_log(self):
        """print the log messages in a friendly one entry / line way"""
        print("Dump of log messages:")
        for line in self.exec_log:
            print(line, file=sys.stderr)


    def save_log(self):
        """Save logs to I have no idea to where at this point"""
        self.print_log()

class ExecEnv:
    """ TheJob() has all important instances we will need during execution.
    Let's run it then."""

    def __init__(self, enable_log):
        self.conf = None
        self.cwd = ""
        self.dl_dir = ""
        self.log = Logger(enable_log)
        self.pipeline_idx = 0
        self.tmp_dir = ""

        self.initialize()

    def check_output(self, cwd, command):
        """Run a command and return it's output"""

        self.log.log(cwd, command)
        stdout = subprocess.check_output(command, shell=True, cwd=cwd)
        stdout = stdout.decode()
        stdout = stdout[:-1] # Remove the newline
        return stdout

    def chmod(self, opts, iscritical=False):
        """call chmod opts"""

        # This is needed to check if the method was called before setconf()
        if self.tmp_dir:
            tmp = self.tmp_dir
        else:
            tmp = "/tmp"

        chmod_cmd = "chmod " + opts

        self.run(tmp, chmod_cmd, iscritical)

    def copy(self, source, target, iscritical=False):
        "Call cp -f"

        # This is needed to check if the method was called before setconf()
        if self.tmp_dir:
            tmp = self.tmp_dir
        else:
            tmp = "/tmp"

        cp_cmd = "cp -f " + source + " " + target

        self.run(tmp, cp_cmd, iscritical)

    def create_file(self, string, path):
        """Equivalent of echo string > path"""

        self.log.log(os.path.dirname(path), "cat " + os.path.basename(path))

        with open(path, "w") as myfp:
            myfp.write(string)

    def download(self, url, filename, iscritical=False):
        """Download the url, save to download_dir/filename and return full path
        to the downloaded file"""

        if not self.dl_dir:
            self.exit("Call " + self.__class__.__name__ +
                      ".setconf() before calling the download method.")


        dl_cmd = "curl -f -s " + url + " > " + filename

        self.run(self.dl_dir, dl_cmd, iscritical)

        return self.dl_dir + "/" + filename

    def exit(self, msg):
        """Does everything needed before exiting such as saving the logs"""

        secs = str(time.time()).split(".")[0]
        self.log.exec_log.append(secs + ":" +  msg + " Exiting...")
        self.log.save_log()
        exit(1)

    def finalize(self):
        """Do this before exiting..."""
        pass

    def initialize(self):
        """Setup the execution environment"""

        # This is needed to check if the method was called before setconf()
        if self.tmp_dir:
            tmp = self.tmp_dir
        else:
            tmp = "/tmp"


    def makedirs(self, path, iscritical=False):
        """Call mkdir -p"""

        # This is needed to check if the method was called before setconf()
        if self.tmp_dir:
            tmp = self.tmp_dir
        else:
            tmp = "/tmp"

        mkdir_cmd = "mkdir -p " + path

        if path[0] != "/":
            self.exit(mkdir_cmd + " Error: relative path not accepted")

        self.run(tmp, mkdir_cmd, iscritical)


    def pipeline(self):
        """Run the commands on the pipeline for each git_in.checkin_target"""
        pass

    def rmtree(self, path, iscritical=False):
        """Remove a directory tree with rm -rf. Use with care!"""

        # This is needed to check if the method was called before setconf()
        if self.tmp_dir:
            tmp = self.tmp_dir
        else:
            tmp = "/tmp"

        rm_cmd = "rm -rf " + path

        if path[0] != "/":
            self.exit(rm_cmd + " Error: relative path not accepted")

        self.run(tmp, rm_cmd, iscritical)

    def run(self, cwd, command_list, iscritical=False):
        """Run the command_list and analyse the $? of each command. If
        isCritical is true, and one of the commands fail, call self.exit()"""

        self.cwd = cwd

        # Just a string, not a list
        if isinstance(command_list, str):
            command_list = [command_list]

        ret_list = self.__call(command_list)

        # Something wrong?
        if iscritical and ret_list.count(0) != len(ret_list):
            index = 0
            log_str = ""
            for ret in ret_list:
                if ret != 0:
                    log_str += "Running " + command_list[index] +\
                               " failed with $? = " + str(ret)
                index += 1

            self.exit(log_str)

    def setconf(self, conf):
        "set self.conf and do some initializations"

        self.conf = conf
        self.tmp_dir = self.conf.conf.get("dir", "tmp_dir")
        self.dl_dir = self.conf.conf.get("dir", "dl_dir")

    def ssh_handshake(self, url):
        """Connect one time to create an entry at ~/.ssh/known_hosts. ssh thinks
        it failed but it didn't, the goal here is just to check the authenticity
        of git_server."""

        # This is needed to check if the method was called before setconf()
        if self.tmp_dir:
            tmp = self.tmp_dir
        else:
            tmp = "/tmp"

        # The command should fail and that's expected
        iscritical = False

        # git@github.com:petersenna/smpl.git => git@github.com
        git_server = url.split(":")[0]

        ssh_cmd = "/usr/bin/ssh -o StrictHostKeyChecking=no " + git_server

        self.run(tmp, ssh_cmd, iscritical)

    def __call(self, command_list):
        """Internal function that uses subprocess.call. This should not be used
        outside this class. Expect a list of strings to be executed.
        Set self.cwd before calling this method."""
        ret_list = []

        for command in command_list:
            print("(cd " + self.cwd + ";" + command + ")", file=sys.stderr)
            ret = subprocess.call(command, shell=True, cwd=self.cwd)
            if ret:
                self.log.log(self.cwd, command, ret)
            else:
                self.log.log(self.cwd, command)

            ret_list.append(ret)

        return ret_list

def main():
    """ Good old main """

    # This isn't the most elegant solution
    myexec = ExecEnv(enable_log=True)
    mycon = JobConfig(myexec)
    myexec.setconf(mycon)
    #print(myexec.download("http://petersenna.com/files/notfound",
    #                      "frampton", iscritical=True))

    mycon.git_in.state.init_by_config()
    mycon.git_out.state.init_by_url()


    #myexec_env.run("/tmp", ["ls -la", "ls -lah", "ls -lah pimba"])
    #myexec_env.run("/tmp", ["ls -la", "ls -lah", "ls -lah pimba"],
    #               iscritical=True)

    #mycon.git_in.state.run("/tmp", ["ls -la", "ls -lah", "ls -lah pimba"])

    #print(myconf.git_in.conf.config_url)
    #print(myconf.git_in.conf.checkout_targets)

    #print(myconf.git_out.conf.repo_url)
    #print(myconf.git_out.conf.compress)
    #print(myconf.git_out.conf.branch_for_write)
    #print(myconf.git_out.ssl_key)

    #for cocci_file in myconf.cocci_files.keys():
    #    print(cocci_file)
    #for script_file in myconf.script_files.keys():
    #    print(script_file)

    #print(myconf.pipeline.pipeline_str)
    #print(myconf.pipeline.stage_count)
    #print(myconf.pipeline.pipeline_stages)

    #print(myconf.git_in.conf.author_name)
    #print(myconf.git_out.conf.author_name)

    #print(myconf.git_in.conf.repo_dir)
    #print(myconf.git_out.conf.repo_dir)
    #print(myconf.git_out.conf.ssl_key_path)

    myexec.exit("That's all folks!")


if __name__ == '__main__':
    main()
