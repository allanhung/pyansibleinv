#!/usr/bin/python

"""
generate ansible inventory for mysql single instance

Usage:
  pyansibleinv aws [--database DATABASE] [--password PASSWORD] [--workdir WORKDIR] [--sshpass SSHPASS] [--sshport SSHPORT] [--sshkey SSHKEY] [--hostarg HOSTARG] [--ssh_try_limit SSHLIMIT] [--taskid TASKID]

Options:
  -h --help                 Show this screen.
  --database DATABASE       Database name create for mysql single instance [default: db1]
  --password PASSWORD       Host password [default: password]
  --workdir WORKDIR         Working Directory [default: /opt/ansible]
  --sshpass SSHPASS         Ansible ssh password
  --sshport SSHPORT         Ansible ssh port [default: 22]
  --sshkey SSHKEY           Ansible ssh key file [default: /opt/ansible/db.pem]
  --ssh_try_limit SSHLIMIT  Wait time for ssh reachable [default: 1800]
  --taskid TASKID           Task id for create mysql single instance
  --hostarg HOSTARG         Ansible hosts additional arguments [default: ]
"""

from docopt import docopt
import common
import os
import sys
import time
from datetime import timedelta
import uuid
import pyansible.playbooks
from subprocess import Popen, PIPE

def gen_inv(args):
    start_time = time.time()
    playbook_template = 'mysql-playbook.j2'
    setting_template = 'mysql-setting-aws.j2'
    ec2_template = 'ec2-instance.j2'
    hosts_script = []
    hosts_script.append('[mysql]')
    mysql_dict={k[2:]:v for k, v in args.items()}
    if args['--taskid']:
        mysql_dict['task_id']='  external_task_id: {}\n'.format(args['--taskid'])
        mysql_dict['uuid']=args['--taskid']
    else:
        mysql_dict['task_id']=''
        mysql_dict['uuid']=str(uuid.uuid4())
    log_filename=os.path.join(mysql_dict['workdir'],'mysql_'+ mysql_dict['uuid']+'.log')
    logger = common.MyLogger('aws', log_filename).default_logger.logger
    logger.info('args:'+str(args))
    mysql_dict['hostname']='mysql-'+mysql_dict['database'].lower()+'-'+mysql_dict['uuid'][:7]
    mysql_dict['ssh_try_limit']=int(args['--ssh_try_limit'])
    # provision ec2 instance
    terraform_cwd = '/opt/terraform/inventory/aws/us-east-1'
    terraform_filename = os.path.join(terraform_cwd,'ec2-'+mysql_dict['hostname']+'.tf')
    logger.info('create terraform file: {}'.format(terraform_filename))
    common.render_template('\n'.join(common.read_template(os.path.join(common.template_dir,ec2_template))),mysql_dict,terraform_filename)   
    p = Popen(['terraform', 'plan'], cwd=terraform_cwd, stdout=PIPE, stderr=PIPE, stdin=PIPE)
    stdout, stderr = p.communicate()
    if p.returncode > 0:
        logger.error('terraform plan error: '+stderr)
        sys.exit()
    else:
        print(stdout)
    p = Popen(['terraform', 'apply', '-auto-approve'], cwd=terraform_cwd, stdout=PIPE, stderr=PIPE, stdin=PIPE)
    stdout, stderr = p.communicate()
    if p.returncode > 0:
        logger.error('terraform apply error: '+stderr)
        sys.exit()
    else:
        print(stdout)
    p = Popen(['terraform', 'output', 'aws_instance_'+mysql_dict['hostname'].replace("-","_")+'_private_ip'], cwd=terraform_cwd, stdout=PIPE, stderr=PIPE, stdin=PIPE)
    stdout, stderr = p.communicate()
    if p.returncode > 0:
        logger.error('terraform output error: '+stderr)
        sys.exit()
    else:
        mysql_dict['ip']=stdout.split('\n')[0]
        print(stdout)

    # post configuration
    playbook_filename=os.path.join(mysql_dict['workdir'],'mysql_'+ mysql_dict['uuid']+'.yml')
    host_filename=os.path.join(mysql_dict['workdir'],'inventory',mysql_dict['uuid'],'hosts')
    setting_filename=os.path.join(mysql_dict['workdir'],'inventory',mysql_dict['uuid'],'pillar','mysql.yml')
    ansible_auth=''
    if mysql_dict['sshpass']:
        ansible_auth='ansible_ssh_pass={}'.format(mysql_dict['sshpass'])
    elif mysql_dict['sshkey']:
        ansible_auth='ansible_ssh_private_key_file={}'.format(mysql_dict['sshkey'])
    hosts_script.append('{:<40}{:<40}{:<50} ansible_ssh_port={:<7} ansible_ssh_user=centos ansible_become=true ansible_become_user=root ansible_become_method=sudo {}'.format(mysql_dict['hostname']+'.useast1.aws', 'ansible_ssh_host='+mysql_dict['ip'], ansible_auth,str(mysql_dict['sshport']), mysql_dict['hostarg']))
    logger.info('create ansible hosts: {}'.format(host_filename))
    common.render_template('\n'.join(hosts_script),{},host_filename)
    logger.info('craete ansible playbooks: {}'.format(playbook_filename))
    common.render_template('\n'.join(common.read_template(os.path.join(common.template_dir,playbook_template))),mysql_dict,playbook_filename)
    logger.info('create mysql single instance setting: {}'.format(setting_filename))
    common.render_template('\n'.join(common.read_template(os.path.join(common.template_dir,setting_template))),mysql_dict,setting_filename)
    logger.info('check ssh availability')
    i=1
    while (not common.check_server(mysql_dict['ip'],int(mysql_dict['sshport']))) and (i < mysql_dict['ssh_try_limit']) :
        time.sleep(1)
        i+=1
    if (not common.check_server(mysql_dict['ip'],int(mysql_dict['sshport']))):
        logger.info('ssh check limit exceed ({} sec): ip {}'.format(mysql_dict['ssh_try_limit'], mysql_dict['ip']))
    logger.info('run ansible from python')
    runner = pyansible.playbooks.Runner(hosts_file=host_filename, playbook_file=playbook_filename, verbosity=3)
    runner.run()
    print("--- Total Excution time: %s ---" % str(timedelta(seconds=(time.time() - start_time))))
    print('You can connect db with:\n    mysql -uroot -p{} -h{} {}'.format(mysql_dict['password'],mysql_dict['ip'],mysql_dict['database']))
    return None
