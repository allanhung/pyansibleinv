#!/usr/bin/python

"""
generate ansible inventory for mssql single instance

Usage:
  pyansibleinv mssql [--database DATABASE] [--dbuser DBUSER] [--password PASSWORD] [--workdir WORKDIR] [--sshuser SSHUSER] [--sshpass SSHPASS] [--sshport SSHPORT] [--ssh_try_limit SSHLIMIT] [--cluster_id CLUSTERID] [--service_name SRVNAME] [--tenant TENANT] [--taskid TASKID] [--template_only] [--without_backup] --hostname HOSTNAME --ip IP

Arguments:
  --hostname HOSTNAME       MSSQL single instance hostname
  --ip IP                   MSSQL IP
Options:
  -h --help                 Show this screen.
  --cluster_id CLUSTERID    MSSQL mha Cluster id
  --service_name SRVNAME    Service Name
  --tenant TENANT           Tenant Name
  --database DATABASE       Database name create for mssql single instance [default: db1]
  --dbuser DBUSER           Database user account [default: dbuser]
  --password PASSWORD       Database user passowrd [default: dbpass]
  --workdir WORKDIR         Working Directory [default: /opt/ansible]
  --sshuser SSHUSER         Ansible winrm username
  --sshpass SSHPASS         Ansible winrm password
  --sshport SSHPORT         Winrm listen port
  --ssh_try_limit SSHLIMIT  test count for ssh reachable (socket timeout is 5 sec) [default: 120]
  --taskid TASKID           Task id for create mssql single instance
  --template_only           Generate template only
  --without_backup          withount backup
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
    playbook_template = 'mssql-playbook.j2'
    setting_template = 'mssql-setting.j2'
    hosts_script = []
    hosts_script.append('[mssql]')
    mssql_dict={k[2:]:v for k, v in args.items()}
    if args['--taskid']:
        mssql_dict['task_id']='  external_task_id: {}\n'.format(args['--taskid'])
        mssql_dict['uuid']=args['--taskid']
    else:
        mssql_dict['task_id']=''
        mssql_dict['uuid']=str(uuid.uuid4())
    log_filename=os.path.join(mssql_dict['workdir'],'mssql_'+ mssql_dict['uuid']+'.log')
    logger = common.MyLogger('mssql', log_filename).default_logger.logger
    logger.info('args:'+str(args))
    mssql_dict['hostname']=args['--hostname'].lower()
    mssql_dict['ip']=args['--ip']
    mssql_dict['ssh_try_limit']=int(args['--ssh_try_limit'])
    mssql_dict['enable_backup']=not args['--without_backup']
    playbook_filename=os.path.join(mssql_dict['workdir'],'mssql_'+ mssql_dict['uuid']+'.yml')
    host_filename=os.path.join(mssql_dict['workdir'],'inventory',mssql_dict['uuid'],'hosts')
    setting_filename=os.path.join(mssql_dict['workdir'],'inventory',mssql_dict['uuid'],'pillar','mssql.yml')
    hosts_script.append("{:<30} ansible_ssh_host={:<20} ansible_ssh_user={:<20} ansible_ssh_pass={:<20} ansible_ssh_port={:<5} ansible_become_pass={:<20} ansible_winrm_transport=ntlm ansible_connection=winrm ansible_winrm_server_cert_validation=ignore".format(mssql_dict['hostname'], mssql_dict['ip'], "'"+mssql_dict['sshuser']+"'", "'"+mssql_dict['sshpass']+"'", str(mssql_dict['sshport']), "'"+mssql_dict['sshpass']+"'"))

    logger.info('create ansible hosts: {}'.format(host_filename))
    common.render_template('\n'.join(hosts_script),{},host_filename)
    logger.info('craete ansible playbooks: {}'.format(playbook_filename))
    common.render_template('\n'.join(common.read_template(os.path.join(common.template_dir,playbook_template))),mssql_dict,playbook_filename)
    logger.info('create mssql single instance setting: {}'.format(setting_filename))
    common.render_template('\n'.join(common.read_template(os.path.join(common.template_dir,setting_template))),mssql_dict,setting_filename)
    if mssql_dict['template_only']:
        print('You can run ansible-playbook -i {} {}'.format(host_filename, playbook_filename))
    else:
        logger.info('check ssh availability')
        i=1
        while (not common.check_server(mssql_dict['ip'],int(mssql_dict['sshport']))) and (i < mssql_dict['ssh_try_limit']) :
            time.sleep(1)
            i+=1
        if (not common.check_server(mssql_dict['ip'],int(mssql_dict['sshport']))):
            logger.info('ssh check limit exceed ({} sec): ip {}'.format(str(mssql_dict['ssh_try_limit']), mssql_dict['ip']))
        logger.info('run ansible from python')
        runner = pyansible.playbooks.Runner(hosts_file=host_filename, playbook_file=playbook_filename, verbosity=3)
        runner.run()
        print("--- wait time for ssh reachable %s sec ---" % str(i))
        print("--- Total Excution time: %s ---" % str(timedelta(seconds=(time.time() - start_time))))
        print('You can connect db with:\n    mssql -uroot -p{} -h{} {}'.format(mssql_dict['password'],mssql_dict['ip'],mssql_dict['database']))
    return None
