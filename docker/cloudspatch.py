#!/usr/bin/env python3
""" This is part of cloudspatch. It reads the configuration file,
get the semantic patch, checkout the correct git repository, run
spatch and commit the result to the output git repository"""
__author__ = "Peter Senna Tschudin"
__email__ = "peter.senna@gmail.com"
__license__ = "GPLv2"
__version__ = "Alpha"

from configparser import ConfigParser, ExtendedInterpolation

def check_config(config):
    """ Check if the configuration file has the minimum parameters"""
    for section in ['com', 'cocci', 'git_out', 'git_in']:
        if section not in config.sections():
            print("Section " + section + " not found in the config file.")

def main():
    """ Good old main """
    config = ConfigParser(interpolation=ExtendedInterpolation())
    config.read("single_job_config")

    check_config(config)

    for sec in config.sections():
        for key in config[sec]:
            print(sec, key, config.get(sec, key))

    print(config.sections()) 

if __name__ == '__main__':
    main()
