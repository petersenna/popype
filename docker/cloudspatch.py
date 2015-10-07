#!/usr/bin/env python3
""" This is part of cloudspatch. It reads the configuration file,
get the semantic patch, checkout the correct git repository, run
spatch and commit the result to the output git repository"""

__author__ = "Peter Senna Tschudin"
__email__ = "peter.senna@gmail.com"
__license__ = "GPLv2"
__version__ = "Alpha"

from configparser import ConfigParser, ExtendedInterpolation
from subprocess import call
import os

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
    result_file = git_out_dir + "/" + job_conf.get("git_out", "result_file")
    result_dir = os.path.dirname(result_file)

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
    if ret == 1:
        ret = 0
    else:
        print("Problem? I'll go on and try to clone $(gitout_repo_url)")

    # Create a directory for using as output
    if not os.path.isdir(git_out_dir):
        os.makedirs(git_out_dir)

    # Finally clone the directory
    ret = call("git clone " + git_url + " .", shell=True, cwd=git_out_dir)
    if ret != 0:
        print("git clone " + git_url + " did not work.")

    # Our branch: check if it exists, if not create it
    # Also create the directory tree and copy the cocci file

    ret = call("git branch -a|grep " + branch, shell=True, cwd=git_out_dir)

    # The branch do not exist
    if ret != 0:
        # Create the branch local and remote
        call("git checkout -b " + branch, shell=True, cwd=git_out_dir)
        call("git push origin " + branch, shell=True, cwd=git_out_dir)

    # The branch does not exist
    else:
        call("git checkout remotes/origin/" + branch,
             shell=True, cwd=git_out_dir)
        call("git checkout -b " + branch, shell=True, cwd=git_out_dir)

    if not os.path.isdir(result_dir):
        # Create the result directory
        os.makedirs(result_dir)

        # Copy and commit the cocci_file
        call("cp /tmp/" + cocci_file + " " + result_dir,
             shell=True, cwd=git_out_dir)
        call("git add " + result_dir + "/" + cocci_file,
             shell=True, cwd=git_out_dir)
        call("git commit -m '$(date)'", shell=True, cwd=git_out_dir)

        # Push the commit to the remote
        ret = call("git push --set-upstream origin  " + branch,
                   shell=True, cwd=git_out_dir)

    return ret

def main():
    """ Good old main """

    job_conf = ConfigParser(interpolation=ExtendedInterpolation())
    job_conf.read("job_conf")

    csp_conf = ConfigParser(interpolation=ExtendedInterpolation())
    csp_conf.read("cloudspatch_conf")

    # Basic check of the job_conf file. Use update_config_check()
    # if you change the job_conf file layout
    if check_job_config(job_conf):
        print("Aborting...")
        exit(1)

    # Step 1: Get the .cocci file and save it at /tmp
    if get_cocci_file(csp_conf, job_conf):
        print("Could not download ${cocci:url}. Aborting...")
        exit(1)

    # Step 2: Configure the git_out repository for saving the results
    if setup_git_out(csp_conf, job_conf):
        print("Could not configure git based on ${git_out:repo_url}...")
        print("Aborting...")
        exit(1)

    #for sec in config.sections():
        #for key in config[sec]:
            #print(sec, key, config.get(sec, key))

if __name__ == '__main__':
    main()
