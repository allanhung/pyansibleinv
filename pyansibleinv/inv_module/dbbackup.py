#!/usr/bin/python

"""
database backup scheduler setting

Usage:
  pyansibleinv dbbackup enable [--db_host DBHOSTS] [--sshpass SSHPASS] [--sshkey SSHKEY] [--ssh_try_limit SSHLIMIT] [--taskid TASKID] --dbtype DBTYPE --dbfqdn DBFQDN
  pyansibleinv dbbackup disable [--db_host DBHOSTS] [--sshpass SSHPASS] [--sshkey SSHKEY] [--ssh_try_limit SSHLIMIT] [--taskid TASKID] --dbtype DBTYPE --dbfqdn DBFQDN
  pyansibleinv dbbackup status [--db_host DBHOSTS] [--sshpass SSHPASS] [--sshkey SSHKEY] [--ssh_try_limit SSHLIMIT] [--taskid TASKID] --dbtype DBTYPE --dbfqdn DBFQDN
  pyansibleinv dbbackup list [--db_host DBHOSTS] [--sshpass SSHPASS] [--sshkey SSHKEY] [--ssh_try_limit SSHLIMIT] [--taskid TASKID] --dbtype DBTYPE --dbfqdn DBFQDN

Arguments:
  --dbtype                  Database type (e.q. mysql, mysql_mha, mssql, mssql_alwayson)
  --dbfqdn                  Database FQDN (e.q. FQDN or FQDN:IP)
Options:
  -h --help                 Show this screen.
  --db_host DBHOSTS         Hosts for database (e.q. hostname1:ip1,hostname2:ip2 ...)
  --sshpass SSHPASS         Ansible ssh password
  --sshkey SSHKEY           Ansible ssh key file [default: /opt/ansible/db.pem]
  --ssh_try_limit SSHLIMIT  Wait time for ssh reachable [default: 1800]
  --taskid TASKID           Task id for create mysql single instance
"""

from docopt import docopt
import common
import os
import time
from datetime import timedelta
import uuid
import pyansible.playbooks

def gen_inv(args):
    print(args)
