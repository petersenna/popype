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
               shell=True, cwd=r'/tmp')

    return ret

def main():
    """ Good old main """
    config = ConfigParser(interpolation=ExtendedInterpolation())
    config.read("single_job_config")

    #update_config_check(config)

    if check_config(config):
        print("Aborting...")
        exit(1)

    if get_cocci_file(config):
        print("Could not download ${cocci:url}. Aborting...")
        exit(1)

    #for sec in config.sections():
        #for key in config[sec]:
            #print(sec, key, config.get(sec, key))

if __name__ == '__main__':
    main()
