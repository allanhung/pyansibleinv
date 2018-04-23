#!/usr/bin/python

"""
database backup scheduler setting

Usage:
  pyansibleinv dbbackup enable [--sshpass SSHPASS] [--sshkey SSHKEY] [--ssh_try_limit SSHLIMIT] [--work_dir WORKDIR] [--taskid TASKID] [--cluster_id CLUSTERID] [--minute MINUTE] [--hour HOUR] [--day DAY] [--month MONTH] [--day_of_week DAYOFWEEK] [--rsets RSETS] [--isets ISETS] --dbtype DBTYPE --data_host DATAHOSTS --dbfqdn DBFQDN
  pyansibleinv dbbackup disable [--db_host DBHOSTS] [--sshpass SSHPASS] [--sshkey SSHKEY] [--ssh_try_limit SSHLIMIT] [--taskid TASKID] [--cluster_id CLUSTERID] --dbtype DBTYPE --dbfqdn DBFQDN
  pyansibleinv dbbackup status [--db_host DBHOSTS] [--sshpass SSHPASS] [--sshkey SSHKEY] [--ssh_try_limit SSHLIMIT] [--taskid TASKID] [--cluster_id CLUSTERID] --dbtype DBTYPE --dbfqdn DBFQDN
  pyansibleinv dbbackup list [--db_host DBHOSTS] [--sshpass SSHPASS] [--sshkey SSHKEY] [--ssh_try_limit SSHLIMIT] [--taskid TASKID] [--cluster_id CLUSTERID] --dbtype DBTYPE --dbfqdn DBFQDN

Arguments:
  --dbtype                  Database type (e.q. mysql, mysql_mha, mssql, mssql_alwayson)
  --dbfqdn                  Database FQDN (e.q. FQDN or FQDN:IP)
  --data_host DATAHOSTS     Hosts (e.q. hostname1:ip1,hostname2:ip2 ...)
Options:
  -h --help                 Show this screen.
  --workdir WORKDIR         Working Directory [default: /opt/ansible]
  --sshpass SSHPASS         Ansible ssh password
  --sshkey SSHKEY           Ansible ssh key file [default: /opt/ansible/db.pem]
  --ssh_try_limit SSHLIMIT  Wait time for ssh reachable [default: 600]
  --cluster_id CLUSTERID    Cluster id
  --taskid TASKID           Task id for create mysql single instance
  --dbtype DBTYPE           db type for backup api
  --dbfqdn DBFQDN           db fqdn for backup api
  --minute MINUTE           Crontab minute [default: 2]
  --hour HOUR               Crontab hour [default: 23]
  --day DAY                 Crontab day [default: *]
  --month MONTH             Crontab month [default: *]
  --day_of_week DAYOFWEEK   Crontab day of week [dafault: *]
  --rsets RSETS             Backup retension sets [default: 3]
  --isets ISETS             Increamental backup in backup retension sets [default: 2]
"""

from docopt import docopt
import common
import os
import time
from datetime import timedelta
import uuid
import pyansible.playbooks
import ara.shell
from StringIO import StringIO
import json

def dbbackup(args, func_type):
    result_dict={}
    start_time = time.time()
    hosts_script = []
    hosts_script.append('[backup]')
    backup_dict = {}

    backup_dict['workdir']=args['--workdir']
    if args['--taskid']:
        backup_dict['task_id']='  external_task_id: {}\n'.format(args['--taskid'])
        backup_dict['uuid']=args['--taskid']
    else:
        backup_dict['uuid']=str(uuid.uuid4())
        backup_dict['task_id']='  external_task_id: {}\n'.format(backup_dict['uuid'])
    backup_dict['dbtype']=args['--dbtype']
    log_filename=os.path.join(backup_dict['workdir'],'dbbackup_%s_%s.log' % (backup_dict['dbtype'], backup_dict['uuid']))
    logger = common.MyLogger('dbbackup_%s_%s' % (backup_dict['dbtype'], backup_dict['uuid']), log_filename.default_logger.logger
    logger.info('args:'+str(args))
    backup_dict['data_hosts']=args['--data_host'].split(",")
    backup_dict['ssh_pass']=args['--sshpass']
    backup_dict['ssh_key']=args['--sshkey']
    backup_dict['ssh_try_limit']=int(args['--ssh_try_limit'])
    backup_dict['dbfqdn']=args['--dbfqdn']
    backup_dict['minute']=args['--minute']
    backup_dict['hour']=args['--hour']
    backup_dict['day']=args['--day']
    backup_dict['month']=args['--month']
    backup_dict['day_of_week']=args['--day_of_week']
    backup_dict['rsets']=args['--rsets']
    backup_dict['isets']=args['--isets']
    playbook_template = 'dbbackup-%s-%s-playbook.j2' % (backup_dict['dbtype'], func_type)
    playbook_filename=os.path.join(backup_dict['workdir'],'dbbackup_'+ backup_dict['uuid']+'.yml')

    host_filename=os.path.join(backup_dict['workdir'],'inventory',backup_dict['uuid'],'hosts')
    if backup_dict['ssh_pass']:
        ansible_auth='ansible_ssh_pass={}'.format(backup_dict['ssh_pass'])
    else:
        ansible_auth='ansible_ssh_private_key_file={}'.format(backup_dict['ssh_key'])

    hostlist=[]
    for i, host_info in enumerate(backup_dict['data_hosts']):
        (k, v) = host_info.split(":")
        k=k.lower()
        host.append(k)
        hosts_script.append('{:<60}{:<60}{}'.format(k, 'ansible_ssh_host='+v, ansible_auth))

    logger.info('create ansible hosts: {}'.format(host_filename))
    common.render_template('\n'.join(hosts_script),{},host_filename)
    logger.info('craete ansible playbooks: {}'.format(playbook_filename))
    common.render_template('\n'.join(common.read_template(os.path.join(common.template_dir,playbook_template))),backup_dict,playbook_filename)
    if backup_dict['--template_only']:
        print('You can run ansible-playbook -i {} {}'.format(host_filename, playbook_filename))
        print("--- Total Excution time: %s ---" % str(timedelta(seconds=(time.time() - start_time))))
    else:
        logger.info('check ssh availability')
        i=1
        for check_ip in ip_list:
            while (not common.check_server(check_ip,22)) and (i < backup_dict['ssh_try_limit']) :
                time.sleep(1)
                i+=1
        for check_ip in ip_list:
            if (not common.check_server(check_ip,22)):
                logger.info('ssh check limit exceed ({} sec): ip {}'.format(str(backup_dict['ssh_try_limit']), check_ip))
        logger.info('run ansible from python')
        runner = pyansible.playbooks.Runner(hosts_file=host_filename, playbook_file=playbook_filename, verbosity=3)
        runner.run()
        print("--- Total Excution time: %s ---" % str(timedelta(seconds=(time.time() - start_time))))
        print('You can connect db with:\n    mysql -uroot -p{} -h{} {}'.format(mha_dict['password'],mha_dict['ip'],mha_dict['database']))

        cli_result = StringIO()
        aracli = ara.shell.AraCli()
        aracli._set_streams(None, cli_result, None)
        for host_info in hostlist:
            cmd = 'data show --playbook %s mybak_%s -f json' % (backup_dict['uuid'], host_info)
            aracli.run(cmd.split(' '))
            result_dict[host_info] = json.loads(cli_result.getvalue())
    return result_dict

def enable(args):
    return dbbackup(args, 'enable')

def diable(args):
    return dbbackup(args, 'enable')

def status(args):
    return dbbackup(args, 'query')

def list(args):
    return dbbackup(args, 'list')

