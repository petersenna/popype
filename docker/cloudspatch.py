#!/usr/bin/env python3
""" This is part of cloudspatch. It reads the configuration file,
get the semantic patch, checkout the correct git repository, run
spatch and commit the result to the output git repository"""

__author__ = "Peter Senna Tschudin"
__email__ = "peter.senna@gmail.com"
__license__ = "GPLv2"
__version__ = "Alpha"

from configparser import ConfigParser, ExtendedInterpolation
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

def get_cocci_file(csp_conf, job_conf):
    """Download the cocci:file and save it at /tmp"""

    dl_dir = csp_conf.get("dir", "cocci_dl_dir")
    cocci_url = job_conf.get("cocci", "url")
    cocci_file = job_conf.get("cocci", "file")
    ret = call("curl -s " + cocci_url + " > " + dl_dir + "/" + cocci_file,
               shell=True, cwd=r"/tmp")

    return ret

def setup_git_out(csp_conf, job_conf):
    """Configure ssh access to git repository for saving the results"""

    id_rsa = csp_conf.get("dir", "id_rsa_dir") + "/id_rsa"

    git_out_dir = csp_conf.get("dir", "git_out_dir")

    branch = job_conf.get("git_out", "branch")
    out_file = git_out_dir + "/" + job_conf.get("git_out", "out_file")
    result_dir = os.path.dirname(out_file)

    cocci_file = job_conf.get("cocci", "file")

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

    # Create a directory for using as output
    if not os.path.isdir(git_out_dir):
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

    if not os.path.isdir(result_dir):
        # Create the result directory
        os.makedirs(result_dir)

        # Copy and commit the cocci_file
        call("cp /tmp/" + cocci_file + " " + result_dir,
             shell=True, cwd=git_out_dir)
        call("git add " + result_dir + "/" + cocci_file,
             shell=True, cwd=git_out_dir)
        call("git commit -m \"$(date)\"", shell=True, cwd=git_out_dir)

        # Push the commit to the remote
        ret = call("git push", shell=True, cwd=git_out_dir)

    return 0

def setup_git_in(csp_conf, job_conf):
    """Configure the code base that will run spatch"""

    linux_dir = csp_conf.get("dir", "linux_dir")
    linux_git_config = linux_dir + "/.git/config"

    dl_dir = csp_conf.get("dir", "tmp_dir")
    dl_git_config = dl_dir + "/config"

    config_url = job_conf.get("git_in", "config_url")
    checkout = job_conf.get("git_in", "checkout")

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

def run_spatch_and_commit(csp_conf, job_conf):
    """Run spatch and commit stdout and stderr to the git repository"""

    nproc = int(check_output(["nproc"]))

    cocci_file = csp_conf.get("dir", "cocci_dl_dir") + "/" +\
                 job_conf.get("cocci", "file")

    cocci_opts = "-j " + str(nproc) + " " + job_conf.get("cocci", "opts")
    git_out_dir = csp_conf.get("dir", "git_out_dir")
    out_file = git_out_dir + "/" + job_conf.get("git_out", "out_file")
    err_file = git_out_dir + "/" + job_conf.get("git_out", "err_file")
    linux_dir = csp_conf.get("dir", "linux_dir")


    # Watch for spaces on string borders, it is needed!
    cmd = "spatch " + cocci_opts + " " + cocci_file + " -dir ."
    print("spatch will run now. Don't expect any output...")
    print("$ cd " + linux_dir + "; " + cmd)
    spatch = Popen(cmd, cwd=linux_dir, shell=True, stdout=PIPE, stderr=PIPE)
    stdout, stderr = spatch.communicate()

    # Pipes make things binary things
    stdout = stdout.decode("ascii")
    stderr = stderr.decode("ascii")

    print(stderr)
    print("spatch exited with code " + str(spatch.returncode))

    with open(err_file, "w") as err_fp:
        err_fp.write(stderr)

    if stdout:
        with open(out_file, "w") as out_fp:
            out_fp.write(stdout)
    else:
        print("stdout is empty, not commiting anything to git_out...")

    call("git add " + out_file + " " + err_file, shell=True, cwd=git_out_dir)
    ret = call("git commit -m \"$(date)\"", shell=True, cwd=git_out_dir)
    if ret != 0:
        print("git commit to git_out failed! Aborting")
        return -1

    ret = call("git push", shell=True, cwd=git_out_dir)
    if ret != 0:
        print("git push to git_out failed! Aborting")
        return -1

    return spatch.returncode

def main():
    """ Good old main """
    # This is configuration file for cloudspatch, with settings that
    # apply to all jobs
    csp_conf = ConfigParser(interpolation=ExtendedInterpolation())
    csp_conf.read("cloudspatch_conf")

    # This is the configuration file describing an specific job.
    job_conf = ConfigParser(interpolation=ExtendedInterpolation())
    job_conf.read("job_conf")

    # Basic check of the job_conf file. You can use update_config_check()
    # if you change the conf file layout
    if check_job_config(job_conf):
        print("Aborting...")
        exit(1)

    # Step 1: Get the .cocci file and save it at
    # csp_config("dir", "cocci_dl_dir")
    if get_cocci_file(csp_conf, job_conf):
        print("Could not download ${cocci:url}. Aborting...")
        exit(1)

    # Step 2: Configure the git_out repository for saving the results
    if setup_git_out(csp_conf, job_conf):
        print("Could not configure git based on ${git_out:repo_url}...")
        print("Aborting...")
        exit(1)

    # Step 3: Configure the code base to run spatch at
    if setup_git_in(csp_conf, job_conf):
        print("Could not configure git based on ${git_in:config_url}...")
        print("Aborting...")
        exit(1)

    # Step 4: Run spatch
    if run_spatch_and_commit(csp_conf, job_conf):
        print("Something went wrong when running spatch.")
        exit(1)

    return 0

if __name__ == '__main__':
    main()
