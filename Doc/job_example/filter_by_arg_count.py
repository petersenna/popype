#!/usr/bin/python
"""This file make a list of functions based on the output of
log_function_names_step2.cocci. It will only print function
names that are called with at least two different number of
arguments. It expect the function list to be at stdin"""
import sys

def main():
    mydict = {}
    mylist = []

    for line in sys.stdin:
        line = line[:-1]
        func, n = line.split(",")

        if func in mydict:
            mydict[func].add(n)
        else:
            mydict[func] = set()
            mydict[func].add(n)

    for func in mydict.keys():
        if len(mydict[func]) >= 2:
            mylist.append(func)

    mylist.sort()
    for func in mylist:
        print func

if __name__ == "__main__":
        main()
