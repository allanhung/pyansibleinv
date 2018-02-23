#!/usr/bin/python

"""
run ansible playbook

Usage:
  pyansibleinv playbook --host HOSTFILE --playbook PLAYBOOK

Arguments:
  --host HOSTFILE           ansible inventory filename
  --playbook PLAYBOOK       ansible playbook filename
Options:
  -h --help                 Show this screen.
"""

from docopt import docopt
import pyansible.playbooks
import common

def gen_inv(args):
    log_filename='playbook.log'
    logger = common.MyLogger('playbook', log_filename).default_logger.logger
    ansible_dict = {}
    ansible_dict['host']=args['--host']
    ansible_dict['playbook']=args['--playbook']

    logger.info('run ansible from python')
    runner = pyansible.playbooks.Runner(hosts_file=ansible_dict['host'], playbook_file=ansible_dict['playbook'], verbosity=3)
    runner.run()
    return None
