#!/usr/bin/env python3
""" This is part of cloudspatch. It reads the configuration file,
get the semantic patch, checkout the correct git repository, run
spatch and commit the result to the output git repository"""

__author__ = "Peter Senna Tschudin"
__email__ = "peter.senna@gmail.com"
__license__ = "GPLv2"
__version__ = "Alpha"

from configparser import ConfigParser, ExtendedInterpolation, NoOptionError
from subprocess import call, check_output, Popen, PIPE
import os, filecmp, shutil

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

def get_cocci_file(csp_conf, job_conf):
    """Download the cocci:file and save it at dl_dir"""

    dl_dir = csp_conf.get("dir", "cocci_dl_dir")
    cocci_name = job_conf.get("cocci", "name")
    cocci_url = ""
    cocci_file = ""

    try:
        cocci_url = job_conf.get("cocci", "url")
    except NoOptionError:
        print("${cocci:url} not found")

    try:
        cocci_file = job_conf.get("cocci", "file")
    except NoOptionError:
        print("${cocci:file} not found")

    if (cocci_url and cocci_file) or (not cocci_url and not cocci_file):
        print("You should use {cocci:url} OR ${cocci:file} on job_config.")
        return -1

    if cocci_url:
        return call("curl -s " + cocci_url + " > " + dl_dir + "/" + cocci_name,
                    shell=True, cwd=r"/tmp")

    if cocci_file:
        with open(dl_dir + "/" + cocci_name, "w") as cocci_fp:
            cocci_fp.write(cocci_file)

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

def run_spatch_and_commit(csp_conf, job_conf, checkout):
    """Run spatch and commit stdout and stderr to the git repository"""

    nproc = int(check_output(["nproc"]))
    linux_dir = csp_conf.get("dir", "linux_dir")
    cocci_file = csp_conf.get("dir", "cocci_dl_dir") + "/" +\
                 job_conf.get("cocci", "name")
    cocci_opts = "-j " + str(nproc) + " " + job_conf.get("cocci", "opts")
    compress = job_conf.get("git_out", "compress")

    # Watch for spaces on string borders, it is needed!
    cmd = "spatch " + cocci_opts + " " + cocci_file + " -dir ."
    print("spatch will run now. Don't expect any output...")
    print("$ cd " + linux_dir + "; " + cmd)
    spatch = Popen(cmd, cwd=linux_dir, shell=True, stdout=PIPE, stderr=PIPE)
    stdout, stderr = spatch.communicate()

    # Do a git pull before doing any changes to git_out
    ret = call("git pull", shell=True, cwd=csp_conf.get("dir", "git_out_dir"))
    if ret != 0:
        print("git pull to git_out failed! Aborting")
        return -1

    # Delay the call to mk_results_dir as much as possible
    results_dir = mk_results_dir(csp_conf, job_conf, checkout)
    out_file = results_dir + "/stdout"
    err_file = results_dir + "/stderr"

    if stderr:
        # Pipes make things binary things
        stderr = stderr.decode("ascii")
        print(stderr)

        with open(err_file, "w") as err_fp:
            err_fp.write(stderr)

        if compress == "xz":
            call("xz " + err_file, shell=True, cwd=results_dir)

        call("git add " + err_file + "*", shell=True, cwd=results_dir)
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

        call("git add " + out_file + "*", shell=True, cwd=results_dir)
    else:
        print("stdout is empty!")

    # The cocci_file is already at results_dir, let's add
    # it for commiting
    call("git add " + job_conf.get("cocci", "name"),
         shell=True, cwd=results_dir)

    ret = call("git commit -m \"$(date)\"", shell=True, cwd=results_dir)
    if ret != 0:
        print("git commit to git_out failed! Aborting")
        return -1

    ret = call("git push", shell=True, cwd=results_dir)
    if ret != 0:
        print("git push to git_out failed! Aborting")
        return -1

    return spatch.returncode

def mk_results_dir(csp_conf, job_conf, checkout):
    """Create the directory for saving the results from spatch, and copy the
    .cocci file to it"""
    cocci_name = job_conf.get("cocci", "name")

    out_dir = csp_conf.get("dir", "git_out_dir") + "/" +\
    job_conf.get("com", "name") + "/" +\
    checkout + "/" + cocci_name.split(".")[0]

    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
        cocci_dl_dir = csp_conf.get("dir", "cocci_dl_dir")
        ret = call("cp " + cocci_dl_dir + "/" + cocci_name + " " + out_dir,
                   shell=True, cwd=out_dir)
        if ret != 0:
            print("Could not copy .cocci file to the destination dir")

    return out_dir

def handle_git_in_checkouts(csp_conf, job_conf):
    """Run spatch in one or more git_in checkouts"""

    all_checkouts = str.split(job_conf.get("git_in", "checkout"), ",")

    for checkout in all_checkouts:
        checkout = checkout.lstrip()
        if setup_git_in(csp_conf, job_conf, checkout):
            print("Could not configure git_in. Not running spatch.")
            print("Aborting...")
            continue
        else:
            if run_spatch_and_commit(csp_conf, job_conf, checkout):
                print("Something went wrong when running spatch.")
                return -1


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

    # Step 2: Get the .cocci file and save it at
    # csp_config("dir", "cocci_dl_dir")
    if get_cocci_file(csp_conf, job_conf):
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
