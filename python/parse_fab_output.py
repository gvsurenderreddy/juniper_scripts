#!/usr/bin/python

"""
    I wasnt able to find SNMP oid/mib to track the fabric's drop on MXes
    so this is the simple script to do it thru the parsing of CLI's output
    to run this script you need to call it like this:
    <scriptname> <path/to/rnames/list> <redis'es hostname/ip>

    rnames list must be formated in such way: each line = router's name
    for example:
    routername1
    routername2
    ...

    also you need to implement your own way to send notificatios
"""

import sys
import subprocess
import redis
from string import join
from send_notification import send_report_email, send_notification

def compare_stats(rdb,rname,high_prio,fpc):
    key = join(('fabric_drop_high:',rname,':fpc:',str(fpc)),'')
    previous_stat = rdb.get(key)
    if previous_stat:
        if previous_stat != high_prio:
            send_notification(rname)
        rdb.set(key,high_prio)
    else:
        rdb.set(key,high_prio)


def parse_fabric_drops(output,rdb,rname):
    output = output.split('FPC')
    fpc_num = 0
    for fpc in output:
        drop_stats = fpc.split('Drop statistics')
        if len(drop_stats) > 1:
            drop_stats = drop_stats[1].split()
            compare_stats(rdb,rname,drop_stats[6],fpc_num)
            fpc_num += 1

def get_fabric_drop_stats(filename):
    rdb = redis.StrictRedis(host=sys.argv[2])
    rnames_fd = open(filename,'r')
    for rname in rnames_fd.readlines():
        rname = rname.split()[0]
        sub_proc=subprocess.Popen(["ssh","-4", rname,
                                   "show class-of-service fabric statistics summary"],
                                   stdout=subprocess.PIPE)
        sp_output=sub_proc.communicate()[0]
        parse_fabric_drops(sp_output,rdb,rname)
    rnames_fd.close()

if __name__ == '__main__':
    get_fabric_drop_stats(sys.argv[1])
 
