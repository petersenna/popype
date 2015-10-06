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

def check_config(config):
    """ Check if the configuration file has the minimum parameters"""

    ret = 0
    for section in ['com', 'cocci', 'git_out', 'git_in']:
        if section not in config.sections():
            print("Section " + section + " not found in the config file.")
            ret = -1

    return ret

def update_config_check(config):
    """Use this function to update the sanity check performed by
    check_config()"""

    for sec in config.sections():
        print(sec + ": " + str(list(config[sec].keys())))

def get_cocci_file(config):
    """Download the cocci:file and save it at /tmp"""

    cocci_url = config.get("cocci", "url")
    cocci_file = config.get("cocci", "file")
    ret = call("curl -s " + cocci_url + " > /tmp/" + cocci_file,
               shell=True, cwd=r"/tmp")

    return ret

def setup_git_out(config):
    """Configure ssh access to git repository for saving the results"""

    id_rsa = "/tmp/id_rsa"
    #id_rsa = "/root/.ssh/id_rsa"

    git_out_dir = "/tmp/git_out"
    #git_out_dir = "/git_out"

    branch = config.get("git_out", "branch")
    result_file = git_out_dir + "/" + config.get("git_out", "result_file")
    result_dir = os.path.dirname(result_file)

    cocci_file = config.get("cocci", "file")

    # Create ~/.ssh for id_rsa
    id_rsa_dir = os.path.dirname(id_rsa)
    if not os.path.isdir(id_rsa_dir):
        os.makedirs(id_rsa_dir)

    # Save the id_rsa aka private key
    with open(id_rsa, "w") as git_key:
        git_key.write(config.get("git_out", "key"))

    # Fix private key permissions
    call("chmod 0600 " + id_rsa, shell=True, cwd=r"/tmp")

    # git@github.com:petersenna/smpl.git
    git_url = config.get("git_out", "repo_url")

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

        # Create the result directory
        os.makedirs(result_dir)

        # Copy and commit the cocci_file
        call("cp /tmp/" + cocci_file + " " + result_dir,
             shell=True, cwd=git_out_dir)
        call("git add " + result_dir + "/" + cocci_file,
             shell=True, cwd=git_out_dir)
        call("git commit -m '$(date)'", shell=True, cwd=git_out_dir)

        # Push the commit to the remote
        ret = call("git push --set-upstream origin  " + branch, shell=True, cwd=git_out_dir)

    # The branch exist
    else:

    return ret

def main():
    """ Good old main """
    config = ConfigParser(interpolation=ExtendedInterpolation())
    config.read("single_job_config")

    # Basic check of the config file. Use update_config_check()
    # if you change the config file layout
    if check_config(config):
        print("Aborting...")
        exit(1)

    # Step 1: Get the .cocci file and save it at /tmp
    if get_cocci_file(config):
        print("Could not download ${cocci:url}. Aborting...")
        exit(1)

    # Step 2: Configure the git_out repository for saving the results
    if setup_git_out(config):
        print("Could not configure git based on ${git_out:repo_url}...")
        print("Aborting...")
        exit(1)

    #for sec in config.sections():
        #for key in config[sec]:
            #print(sec, key, config.get(sec, key))

if __name__ == '__main__':
    main()
