#!/usr/bin/python

"""
generate ansible inventory for mysql single instance

Usage:
  pyansibleinv mysql [--database DATABASE] [--password PASSWORD] [--workdir WORKDIR] --taskid TASKID --hostname HOSTNAME --ip IP

Arguments:
  --hostname HOSTNAME       MySQL single instance hostname
  --ip IP                   MySQL IP
  --taskid TASKID           Task id for create mysql single instance
Options:
  -h --help                 Show this screen.
  --database DATABASE       Database name create for mysql single instance [default: db1]
  --password PASSWORD       Host password [default: password]
  --workdir WORKDIR         Working Directory [default: /opt/ansible]
"""

from docopt import docopt
import common
import os
import pyansible.playbooks

filename = '/opt/ansible/hosts'
try:
    temp = open(filename, 'w+b')
    temp.write("[mysql]\n")
    temp.write("{} ansible_ssh_host={} ansible_connection=local".format(sys.argv[1], sys.argv[2]))
finally:
    temp.close()

try:

def gen_inv(args):
    playbook_template = 'mysql-playbook.j2'
    setting_template = 'mysql-setting.j2'
    hosts_script = []
    hosts_script.append('[mysql]')
    mysql_dict = {}
    mysql_dict['database']=args['--database']
    mysql_dict['password']=args['--password']
    mysql_dict['workdir']=args['--workdir']
    mysql_dict['task_id']=args['--taskid']
    mysql_dict['hostname']=args['--hostname']
    mysql_dict['ip']=args['--ip']
    host_filename=os.path.join(mysql_dict['workdir'],'inventory',mysql_dict['task_id'],'hosts')
    playbook_filename=os.path.join(mysql_dict['workdir'],'mysql_'+ mysql_dict['task_id']+'.yml')
    setting_filename=os.path.join(mysql_dict['workdir'],'inventory',mysql_dict['task_id'],'pillar','mysql.yml')
    hosts_script.append('{:<30}{:<30}{}'.format(mysql_dict['hostname'], 'ansible_ssh_host='+mysql_dict['ip'], 'ansible_ssh_private_key_file=/opt/ansible/db.pem'))

    print('create ansible hosts: {}'.format(host_filename))
    common.render_template('\n'.join(hosts_script),{},host_filename)
    print('craete ansible playbooks: {}'.format(playbook_filename))
    common.render_template('\n'.join(common.read_template(os.path.join(common.template_dir,playbook_template))),mysql_dict,playbook_filename)
    print('create mysql single instance setting: {}'.format(setting_filename))
    common.render_template('\n'.join(common.read_template(os.path.join(common.template_dir,setting_template))),mysql_dict,setting_filename)
    print('run ansible from python')
    runner = pyansible.playbooks.Runner(hosts_file=host_filename, playbook_file=playbook_filename, verbosity=3)
    runner.run()
    return None
