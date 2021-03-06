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

from configparser import ConfigParser, ExtendedInterpolation, NoOptionError
from subprocess import call, check_output, Popen, PIPE
import os, filecmp, shutil


class GitRepo:
    """A git repository"""
    def __init__(self):


class Cocci:
    """.cocci file on the pipeline"""
    def __init__(self):

class Script:
    """script on the pipeline"""
    def __init__(self):

class Pipeline:
    """An example pipeline:

          step1.cocci|finalize1.py|step2.cocci|post.py

          *.cocci apply the semantic patch on each checkout of linus.git
          *.py apply the script to stdout of previous semantic patch
             it will create one directory with the branch name: branch
                one directory for each checkout: v4.2
                   one directory for each stage of the pipeline: step1,
                   finalize1, step2, post
            branch/v4.2/{step1, finalize1, step2, post}
    Will also print the last stdout of the pipeline before exiting"""

    def __init__(self):
        git_in = GitRepo()
        git_out = GitRepo()
        cocci_scripts = Cocci()
        scripts = Script()


def utopic_test():

    pl = Pipeline()

    # Pipeline.GitRepo accept an URL to a git config file
    pl.git_in = Pipeline.GitRepo("http://github.com/petersenna/cocci-linux-git/config")
    pl.git_in.checkout = """v2.6.12, v2.6.15, v2.6.20, v2.6.25, v2.6.30,
            v2.6.35, v3.0, v3.10, v3.15, v3.5, v4.0, v4.2"""
    # This would be nice!
    pl.git_in.checkout_regex = "^v2\.6\.[0-9]*$|^v[34]\.[0-9]*$"

    # Pipeline.GitRepo accept an URL to a git repository
    pl.git_out = Pipeline.GitRepo("git@github.com:petersenna/fake.git")
    pl.git_out.ssh_key = """-----BEGIN RSA PRIVATE KEY-----
            MIIEpAIBAAKCAQEA7SQQS+WTFO67OgZ1PGMo2fUtc81K2x/7gbz3Ln30bOuCbFLm
            +/oqToouhhLdd0o9Oe9JZ7m39LcIjl7tbZEQ2QxAHk/946vhrwUVBNX+fq6mwAGP
            GcU3FEjL7JirAjv6rd61VHx/hxUFEdt+MZ57lxPKONRG8RxB43Uh2TtXxvSXrkLe
            8DXY5nTAQHHPaR6U0FsfzuhKSXE7OpXk4OqnbI14CCRsnav7XoB8XY2E7y5ju/Er
            MMoL7G5MSN4CgGQ71XFHmCNzOgw3dlEzxWOgLmYpy7iY/4PpYbtdpHMEAPqPz6YW
            cskSqg2GAoKY9XePPHNz2jNsFSB3riT/jQBFowIDAQABAoIBABc4LcRQsUseaQSw
            dzA3gVt+DzpEgqzb/9NfPlC2EoXLtZSHtYg8oYHZM9763+Z7RW1zyZs3axSyC0tt
            bhAJYT3vXiPZr0FopgtuEvXLQkUDMt6gCHP8hH0e96Ct/iiU2OHHabfhDNecLkfm
            Vv/ixbUwQd+4oU2gd68e2/aaQej//8kgqA0zVqxktXtDRcAWrrOnJ4x52mo+VoKi
            AEkgy5vwtC0tPqc9/GceKO2Brtudv7Q3B6JvTe8rlMHr9lUrHh7LINuWDiGlNx5T
            S+3YmlLtBTdk2Fir33KPGb3y99pfrCVFyBJhntBpW4HeMMrRYr88nJqSSP303HiS
            /ddMkJECgYEA/U8AC6ZqjvUqi1N2v9I0wQmUT6h6LpDX6dGBrseUzs5Vj2+WTWmH
            Wqooe/JuRtKfFyWpwepchjeaPcA/n8HoujkRWtiXSF8b4uqTJCgkGlDfN3WtRwKZ
            9Zq+euB3iLhEOXtE93mpL7d4EfrX/6Yhc+9SYYHOsuYEinf3jBJUwGsCgYEA76kW
            VhtDGHwQ4k5paEJwwdnFm7RG+gG8CR+nTcp2K7pUyYXynyoQdJ4PePOdc+qrA0Nj
            yCobAbfMwlDl3ZzLPjGHUGo3uRbivF5Tktwjyi7HDPgC8+/mUTEfvb3uFcesit9L
            FfNaKfUria70Qb3+y8SEiKnmwWR+P5NPyIWLfakCgYEA8kz8LSitqzumy4k2APzx
            C2m/XYc6AIr6jaWjF+2/UScbvs2thzUXjUlQ2mcmx0Y3eavEO0KT6KsNNl5MPeP9
            Wwy1piGibE7V3PQndaGUDzwmmOVOr6s0XDP+WomWrcgdMqLQcK0GgidMil5Y+SkP
            vNdDBRRnBMdztoRU3b63JSsCgYByXmOtZccoKRS5mqfMvGAo8i7ONkLkze0ZAYUK
            p4KrLXmGzihRcnZ14HQLyV4rUiKYJRG6FPXcZQUO+iIoFsoa/PHRG09KQbSkJfOG
            Ew31T0toUfa+yI5F0saN+tRiim45u4OOjxpJCZnkU5x2vx+XyEljGolnYvioiDk7
            vRcrOQKBgQCxaX/FDHoWL6ZMf+CqBwN7Sr0n2JXkVVQjpp7LZ2TQiB3L3TSoIAK4
            k9Wujr1dD5J0jZZy4/wIE9E/yVOF+EvizaOLiFaqXtgmAEXq9k9Cbq1V1z/IGMm+
            fMvZmIy+WPp/77d24/iCwnljKJ4XTNR25Bl8H8NKhTvaIIhlznrrcA==
            -----END RSA PRIVATE KEY-----"""
    pl.git_out.branch = "test-20151016"
    pl.git_out.author = "Peter Senna Tschudin"
    pl.git_out.email = "peter.senna@gmail.com"

    # Pipeline.Cocci accept a file name or URL
    pl.log_in_if_cocci = Pipeline.Cocci("log_in_if.cocci")
    pl.log_in_if_cocci.opts = "--timeout 120"
    pl.log_in_if_cocci.compress = True
    pl.log_in_if_cocci.parallel = True

    # Pipeline.Cocci accept a file name or URL
    pl.log_num_args_cocci = Pipeline.Cocci("log_num_args.cocci")
    pl.log_num_args_cocci.opts = "--timeout 120"
    pl.log_num_args_cocci.compress = True
    pl.log_num_args_cocci.parallel = True

    # Pipeline.Cocci accept a file name or URL
    pl.log_f_call_cocci = Pipeline.Cocci("log_f_call.cocci")
    pl.log_f_call_cocci.opts = "--timeout 120"
    pl.log_f_call_cocci.compress = True
    pl.log_f_call_cocci.parallel = True

    # Pipeline.Script accept a file name or URL
    pl.filter_by_num_args_sc = Pipeline.Script("filter_by_num_args.py")
    pl.filter_by_num_args_sc.compress = "gz"

    # Pipeline.Script accept a file name or URL
    pl.count_f_calls_sc = Pipeline.Script("count_f_calls.py")
    pl.count_f_calls_sc.compress = "gz"
    
    pl.run("""git_in: log_in_if_cocci | log_num_args_cocci |
            filter_by_num_args_sc | log_f_call_cocci |
            count_f_calls_sc > git_out""")



def check_job_config(job_conf):
    """ Check if the configuration file has the minimum parameters"""

    ret = 0
    for section in ['com', 'cocci', 'git_out', 'git_in']:
        if section not in job_conf.sections():
            print("Section " + section + " not found in the config file.")
            ret = -1

    return ret

def update_config_check(config):
    """Use this function to update the sanity check performed by
    check_config()"""

    for sec in config.sections():
        print(sec + ": " + str(list(config[sec].keys())))

def configure_git_env(csp_conf, job_conf):
    """ Configure git author and E-mail for commiting"""

    author = job_conf.get("com", "author")
    email = job_conf.get("com", "email")

    tmp_dir = csp_conf.get("dir", "tmp_dir")

    print("configuring git user.name and git user.email...")
    call("git config --global user.name \"" + author + "\"",
         shell=True, cwd=tmp_dir)
    call("git config --global user.email \"" + email + "\"",
         shell=True, cwd=tmp_dir)
    call("git config --global push.default simple", shell=True, cwd=tmp_dir)

    return 0

def get_cocci_files(csp_conf, job_conf):
    """Download the cocci files and save it at dl_dir"""

    dl_dir = csp_conf.get("dir", "cocci_dl_dir")
    if dl_dir[-1] != "/":
        dl_dir += "/"

    all_cocci_name = ""
    cocci_url = ""

    try:
        all_cocci_name = job_conf.get("cocci", "name")
    except NoOptionError:
        print("${cocci:name} not found")
        return -1

    try:
        cocci_url = job_conf.get("cocci", "url")
    except NoOptionError:
        print("${cocci:url} not found")
        return -1

    if cocci_url[-6:] == ".cocci":
        print("Your $(cocci:url) is probably wrong as it is ending with .cocci")
        print("If the download fails, check $(cocci:url) and $(cocci:name).")

    if cocci_url[-1] != "/":
        cocci_url += "/"

    all_cocci_names = str.split(all_cocci_name, ",")

    for cocci_name in all_cocci_names:
        cocci_name = cocci_name.lstrip()
        ret = call("curl -s " + cocci_url + cocci_name + " > " + dl_dir +\
                cocci_name, shell=True, cwd=r"/tmp")
        if ret != 0:
            print("Download of the .cocci file failed: " +\
                    cocci_url + cocci_name)
            return -1

    # Pasting the .cocci file on the job_conf is not supported at this time
    #try:
    #    cocci_file = job_conf.get("cocci", "file")
    #except NoOptionError:
    #    print("${cocci:file} not found")
    #
    #if (cocci_url and cocci_file) or (not cocci_url and not cocci_file):
    #    print("You should use {cocci:url} OR ${cocci:file} on job_config.")
    #    return -1
    #if cocci_file:
    #    with open(dl_dir + "/" + cocci_name, "w") as cocci_fp:
    #        cocci_fp.write(cocci_file)

    return 0

def setup_git_out(csp_conf, job_conf):
    """Configure ssh access to git repository for saving the results"""

    id_rsa = csp_conf.get("dir", "id_rsa_dir") + "/id_rsa"

    git_out_dir = csp_conf.get("dir", "git_out_dir")

    branch = job_conf.get("git_out", "branch")

    # Create ~/.ssh for id_rsa
    id_rsa_dir = os.path.dirname(id_rsa)
    if not os.path.isdir(id_rsa_dir):
        os.makedirs(id_rsa_dir)

    # Save the id_rsa aka private key
    with open(id_rsa, "w") as git_key:
        git_key.write(job_conf.get("git_out", "key"))

    # Fix private key permissions
    call("chmod 0600 " + id_rsa, shell=True, cwd=r"/tmp")

    # git@github.com:petersenna/smpl.git
    git_url = job_conf.get("git_out", "repo_url")

    # becomes: git@github.com
    git_server = git_url.split(":")[0]

    # Connect one time to create an entry at ~/.ssh/known_hosts.
    # ssh thinks it failed but it didn't, the goal here is just
    # to check the authenticity of git_server
    ret = call("/usr/bin/ssh -o StrictHostKeyChecking=no " + git_server,
               shell=True, cwd=r"/tmp")
    if ret != 1:
        print("Problem? I'll go on and try to clone $(gitout_repo_url)")

    # This directory should not exist, delete if it is there
    if os.path.exists(git_out_dir):
        shutil.rmtree(git_out_dir)
    os.makedirs(git_out_dir)

    # Finally clone the directory
    ret = call("git clone " + git_url + " .", shell=True, cwd=git_out_dir)
    if ret != 0:
        print("git clone " + git_url + " did not work.")
        return -1

    # Our branch: check if it exists, if not create it
    # Also create the directory tree and copy the cocci file

    ret = call("git branch -a|grep " + branch, shell=True, cwd=git_out_dir)

    # The branch do not exist
    if ret != 0:
        # Create the branch local and remote
        call("git checkout -b " + branch, shell=True, cwd=git_out_dir)
        call("git push origin " + branch, shell=True, cwd=git_out_dir)

    # The branch already exist
    else:
        call("git checkout remotes/origin/" + branch,
             shell=True, cwd=git_out_dir)
        call("git checkout -b " + branch, shell=True, cwd=git_out_dir)

    # Track the remote branch
    call("git branch -u origin/" + branch, shell=True, cwd=git_out_dir)

    ret = call("git push --dry-run", shell=True, cwd=git_out_dir)
    if ret != 0:
        print("No write access to git_out...")
        return -1

    return 0

def setup_git_in(csp_conf, job_conf, checkout):
    """Configure the code base that will run spatch"""

    linux_dir = csp_conf.get("dir", "linux_dir")
    linux_git_config = linux_dir + "/.git/config"

    dl_dir = csp_conf.get("dir", "tmp_dir")
    dl_git_config = dl_dir + "/config"

    config_url = job_conf.get("git_in", "config_url")

    ret = call("curl -s " + config_url + " > " + dl_git_config,
               shell=True, cwd=r"/tmp")
    if ret != 0:
        print("Could not download the config file for the git repository")
        return -1

    linux_git_config_exist = os.path.exists(linux_git_config)
    if linux_git_config_exist:
        git_configs_match = filecmp.cmp(dl_git_config, linux_git_config)

    if not linux_git_config_exist:
        os.makedirs(os.path.dirname(linux_git_config))

    if linux_git_config_exist and not git_configs_match:
        # Wrong config file, delete it all and start again
        shutil.rmtree(linux_dir)
        os.makedirs(os.path.dirname(linux_git_config))

    call("cp -f " + dl_git_config + " " + linux_git_config,
         shell=True, cwd=r"/tmp")
    call("git init .", shell=True, cwd=linux_dir)

    ret = call("git remote update", shell=True, cwd=linux_dir)
    if ret != 0:
        print("Could not update remotes. Network ok? .git/config ok?")
        return -1

    # git reset --hard; git clean -f -x -d; git checkout ...
    call("git reset --hard", shell=True, cwd=linux_dir)
    call("git clean -f -x -d", shell=True, cwd=linux_dir)
    ret = call("git checkout " + checkout, shell=True, cwd=linux_dir)
    if ret != 0:
        print("Could not checkout. Something is wrong...")
        return -1

    return 0

def delete_files_if_exist(files):
    """Delete all files that on the list"""

    for one_file in files:
        if os.path.exists(one_file):
            os.remove(one_file)

def run_spatch_and_commit(csp_conf, job_conf, checkout, cocci_name):
    """Run spatch and commit stdout and stderr to the git repository"""

    nproc = int(check_output(["nproc"]))
    linux_dir = csp_conf.get("dir", "linux_dir")
    cocci_file = csp_conf.get("dir", "cocci_dl_dir") + "/" + cocci_name

    # Call the first time here
    results_dir = mk_results_dir(csp_conf, job_conf, checkout, cocci_name)

    cocci_opts = "-j " + str(nproc) + " " + job_conf.get("cocci", "opts") +\
    " -D checkout=" + checkout + " -D results_dir=" + results_dir

    compress = job_conf.get("git_out", "compress")

    # Watch for spaces on string borders, it is needed!
    cmd = "spatch " + cocci_opts + " " + cocci_file + " -dir ."
    print("spatch will run now. Don't expect any output...")
    print("$ cd " + linux_dir + "; " + cmd)
    spatch = Popen(cmd, cwd=linux_dir, shell=True, stdout=PIPE, stderr=PIPE)
    stdout, stderr = spatch.communicate()

    # Do a git pull before doing any changes to git_out
    ret = call("git pull --no-edit", shell=True,\
            cwd=csp_conf.get("dir", "git_out_dir"))
    if ret != 0:
        print("git pull to git_out failed! Aborting")
        return -1

    # Yes, run it again!
    results_dir = mk_results_dir(csp_conf, job_conf, checkout, cocci_name)
    out_file = results_dir + "/stdout"
    err_file = results_dir + "/stderr"

    # Delete files before continuing
    delete_files_if_exist([out_file, err_file])

    if compress:
        delete_files_if_exist([out_file + ".xz", err_file + ".xz"])

    if stderr:
        # Pipes make things binary things
        stderr = stderr.decode("ascii")
        print(stderr)

        with open(err_file, "w") as err_fp:
            err_fp.write(stderr)

        if compress == "xz":
            call("xz " + err_file, shell=True, cwd=results_dir)
            call("git add " + err_file + ".xz", shell=True, cwd=results_dir)
        else:
            call("git add " + err_file, shell=True, cwd=results_dir)

    else:
        print("stderr is empty!")

    print("spatch exited with code " + str(spatch.returncode))

    if stdout:
        # Pipes make things binary things
        stdout = stdout.decode("ascii")
        with open(out_file, "w") as out_fp:
            out_fp.write(stdout)

        if compress == "xz":
            call("xz " + out_file, shell=True, cwd=results_dir)
            call("git add " + out_file + ".xz", shell=True, cwd=results_dir)
        else:
            call("git add " + out_file, shell=True, cwd=results_dir)

    else:
        print("stdout is empty!")

    # The cocci_file is already at results_dir, let's add
    # it for commiting
    call("git add " + cocci_name, shell=True, cwd=results_dir)

    ret = call("git commit -m \"$(date)\"", shell=True, cwd=results_dir)
    if ret != 0:
        print("git commit to git_out failed! Aborting")
        return -1

    ret = call("git push", shell=True, cwd=results_dir)
    if ret != 0:
        print("git push to git_out failed! Aborting")
        return -1

    return spatch.returncode

def get_results_dir(csp_conf, job_conf, checkout, cocci_name):
    """what is the out_dir?"""

    out_dir = csp_conf.get("dir", "git_out_dir") + "/" +\
              job_conf.get("com", "name") + "/" +\
              checkout + "/" + cocci_name.split(".")[0]

    return out_dir

def mk_results_dir(csp_conf, job_conf, checkout, cocci_name):
    """Create the directory for saving the results from spatch, and copy the
    .cocci file to it"""

    out_dir = get_results_dir(csp_conf, job_conf, checkout, cocci_name)

    cocci_dl_full_path = csp_conf.get("dir", "cocci_dl_dir") + "/" + cocci_name

    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    ret = call("cp -f " + cocci_dl_full_path + " " + out_dir,
               shell=True, cwd=out_dir)
    if ret != 0:
        print("Could not copy .cocci file to the destination dir")

    return out_dir

def handle_git_in_checkouts(csp_conf, job_conf):
    """Run spatch in one or more git_in checkouts for
    one or more cocci_files"""

    all_checkouts = str.split(job_conf.get("git_in", "checkout"), ",")
    all_cocci_names = str.split(job_conf.get("cocci", "name"), ",")

    for checkout in all_checkouts:
        checkout = checkout.lstrip()
        if setup_git_in(csp_conf, job_conf, checkout):
            print("Could not configure git_in. Not running spatch.")
            print("Aborting...")
            continue
        else:
            for cocci_name in all_cocci_names:
                cocci_name = cocci_name.lstrip()
                if run_spatch_and_commit(csp_conf, job_conf, checkout,\
                        cocci_name):
                    print("Something went wrong when running spatch.")
                    print("I'll try the next one...")

def check_job_url(csp_conf, job_conf):
    """Checks if the user specified an url"""
    try:
        cocci_url = job_conf.get("cocci", "url")
    except NoOptionError:
        print("${cocci:url} not specifyed. I'll use local .cocci files...")
        return False

    return True

def get_pending_checkout(csp_conf, job_conf):
    # Two files are used in the task directory for controlling tasks
    # that are being processed and tasks that are concluded.
    all_checkouts = str.split(job_conf.get("git_in", "checkout"), ",")
    checkouts_done = {}
    checkouts_running = {}


def handle_git_in_checkouts_yeah(csp_conf, job_conf):
    """Run spatch in one or more git_in checkouts, but check which checkouts
    are being processed at the moment and which are already done"""

    while checkout = get_pending_checkout(csp_conf, job_conf):
        if setup_git_in(csp_conf, job_conf, checkout):
            print("Could not configure git_in. Not running spatch.")
            print("Aborting...")
            continue
        else:
            if run_spatch_and_commit(csp_conf, job_conf, checkout):
                print("Something went wrong when running spatch.")
                print("I'll try the next one...")

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

    # This is the configuration file describing an specific job.
    job_conf = ConfigParser(interpolation=ExtendedInterpolation())
    job_conf.read("job_conf")

    # Basic check of the job_conf file. You can use update_config_check()
    # if you change the conf file layout
    if check_job_config(job_conf):
        print("Aborting...")
        exit(1)

    # Step 1: Configure git environment variables
    if configure_git_env(csp_conf, job_conf):
        print("Could not configure git user and email for commiting...")
        exit(1)

    # Step 2: Optional: If ${cocci:url} is defined download the .cocci files
    # and save it at csp_config("dir", "cocci_dl_dir")
    if check_job_url(csp_conf, job_conf):
        if get_cocci_files(csp_conf, job_conf):
            print("Could not get the .cocci file. Aborting...")
            exit(1)

    # Step 3: Configure the git_out repository for saving the results
    if setup_git_out(csp_conf, job_conf):
        print("Could not configure git based on ${git_out:repo_url}...")
        print("Aborting...")
        exit(1)

    # Step 4: checkout, run spatch, and commit to git_out for each
    # ${git_in:checkout}
    if handle_git_in_checkouts(csp_conf, job_conf):
        print("Could not run everything...")
        print("Aborting...")
        exit(1)

    return 0

if __name__ == '__main__':
    main()
