#!/usr/bin/python
"""Compute the number of function calls based on stdin. Expects CSV with
function name as first argument and position metavariable fields as other
arguments:

printk,3,9,configfs_example_init,configfs_example_explicit.c,457,457"""

import sys
import re
def main():
    mydict = {}
    mylist = []

    specialized_funcs_regex = "(^pr_|^ata_|^dev|^fs_|^hid_|^net|^v4l)"
    calls = 0
    printk_calls = 0
    specialized_calls = 0
    other_calls = 0

    for line in sys.stdin:
        line = line[:-1]
        func = line.split(",")[0]

        calls += 1

        if re.match(specialized_funcs_regex, func):
            specialized_calls += 1
        elif func == "printk":
            printk_calls += 1
        else:
            other_calls += 1

        if func in mydict:
            mydict[func] += 1
        else:
            mydict[func] = 1

    for func in mydict.keys():
        mylist.append(func + "," + str(mydict[func]))

    mylist.sort()
    for func in mylist:
        print func

    print "=printk_calls: " + str(printk_calls)
    print "=specialized_calls" + specialized_funcs_regex + ": " +\
            str(specialized_calls)
    print "=other_calls: " + str(other_calls)
    print "=total_calls: " + str(calls)

if __name__ == "__main__":
        main()
