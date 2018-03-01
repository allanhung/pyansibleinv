#!/usr/bin/python

"""
generate ansible inventory for mysql single instance

Usage:
  pyansibleinv mysql [--database DATABASE] [--password PASSWORD] [--workdir WORKDIR] [--sshpass SSHPASS] [--sshkey SSHKEY] [--taskid TASKID] --hostname HOSTNAME --ip IP

Arguments:
  --hostname HOSTNAME       MySQL single instance hostname
  --ip IP                   MySQL IP
Options:
  -h --help                 Show this screen.
  --database DATABASE       Database name create for mysql single instance [default: db1]
  --password PASSWORD       Host password [default: password]
  --workdir WORKDIR         Working Directory [default: /opt/ansible]
  --sshpass SSHPASS         Ansible ssh password
  --sshkey SSHKEY           Ansible ssh key file [default: /opt/ansible/db.pem]
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
    start_time = time.time()
    playbook_template = 'mysql-playbook.j2'
    setting_template = 'mysql-setting.j2'
    hosts_script = []
    hosts_script.append('[mysql]')
    mysql_dict = {}
    mysql_dict['database']=args['--database']
    mysql_dict['password']=args['--password']
    mysql_dict['workdir']=args['--workdir']
    if args['--taskid']:
        mysql_dict['task_id']='  external_task_id: {}\n'.format(args['--taskid'])
        mysql_dict['uuid']=args['--taskid']
    else:
        mysql_dict['task_id']=''
        mysql_dict['uuid']=str(uuid.uuid4())
    log_filename=os.path.join(mysql_dict['workdir'],'mysql_'+ mysql_dict['uuid']+'.log')
    logger = common.MyLogger('mysql', log_filename).default_logger.logger
    mysql_dict['hostname']=args['--hostname']
    mysql_dict['ip']=args['--ip']
    mysql_dict['ssh_pass']=args['--sshpass']
    mysql_dict['ssh_key']=args['--sshkey']
    playbook_filename=os.path.join(mysql_dict['workdir'],'mysql_'+ mysql_dict['uuid']+'.yml')
    host_filename=os.path.join(mysql_dict['workdir'],'inventory',mysql_dict['uuid'],'hosts')
    setting_filename=os.path.join(mysql_dict['workdir'],'inventory',mysql_dict['uuid'],'pillar','mysql.yml')
    if mysql_dict['ssh_pass']:
        ansible_auth='ansible_ssh_pass={}'.format(mysql_dict['ssh_pass'])
    else:
        ansible_auth='ansible_ssh_private_key_file={}'.format(mysql_dict['ssh_key'])
    hosts_script.append('{:<60}{:<60}{}'.format(mysql_dict['hostname'], 'ansible_ssh_host='+mysql_dict['ip'], ansible_auth))

    logger.info('create ansible hosts: {}'.format(host_filename))
    common.render_template('\n'.join(hosts_script),{},host_filename)
    logger.info('craete ansible playbooks: {}'.format(playbook_filename))
    common.render_template('\n'.join(common.read_template(os.path.join(common.template_dir,playbook_template))),mysql_dict,playbook_filename)
    logger.info('create mysql single instance setting: {}'.format(setting_filename))
    common.render_template('\n'.join(common.read_template(os.path.join(common.template_dir,setting_template))),mysql_dict,setting_filename)
    logger.info('check ssh availability')
    while not common.check_server(mysql_dict['ip'],22):
        time.sleep(1)
    logger.info('run ansible from python')
    runner = pyansible.playbooks.Runner(hosts_file=host_filename, playbook_file=playbook_filename, verbosity=3)
    runner.run()
    print("--- Total Excution time: %s ---" % str(timedelta(seconds=(time.time() - start_time))))
    print('You can connect db with:\n    mysql -uroot -p{} -h{} {}'.format(mysql_dict['password'],mysql_dict['ip'],mysql_dict['database']))
    return None
