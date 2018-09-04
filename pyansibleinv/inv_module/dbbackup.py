#!/usr/bin/python

"""
database backup scheduler setting

Usage:
  pyansibleinv dbbackup enable [--sshpass SSHPASS] [--sshport SSHPORT] [--sshkey SSHKEY] [--hostarg HOSTARG] [--ssh_try_limit SSHLIMIT] [--workdir WORKDIR] [--taskid TASKID] [--cluster_id CLUSTERID] [--service_name SRVNAME] [--tenant TENANT] [--minute MINUTE] [--hour HOUR] [--day DAY] [--month MONTH] [--day_of_week DAYOFWEEK] [--rsets RSETS] [--isets ISETS] [--template_only] --dbtype DBTYPE --data_host DATAHOSTS --dbfqdn DBFQDN
  pyansibleinv dbbackup disable [--sshpass SSHPASS] [--sshport SSHPORT] [--sshkey SSHKEY] [--hostarg HOSTARG] [--ssh_try_limit SSHLIMIT] [--workdir WORKDIR] [--taskid TASKID] [--cluster_id CLUSTERID] [--service_name SRVNAME] [--tenant TENANT] [--template_only] --dbtype DBTYPE --data_host DATAHOSTS --dbfqdn DBFQDN
  pyansibleinv dbbackup status [--sshpass SSHPASS] [--sshport SSHPORT] [--sshkey SSHKEY] [--hostarg HOSTARG] [--ssh_try_limit SSHLIMIT] [--workdir WORKDIR] [--taskid TASKID] [--cluster_id CLUSTERID] [--service_name SRVNAME] [--tenant TENANT] [--template_only] --dbtype DBTYPE --data_host DATAHOSTS --dbfqdn DBFQDN
  pyansibleinv dbbackup listx [--sshpass SSHPASS] [--sshport SSHPORT] [--sshkey SSHKEY] [--hostarg HOSTARG] [--ssh_try_limit SSHLIMIT] [--workdir WORKDIR] [--taskid TASKID] [--cluster_id CLUSTERID] [--service_name SRVNAME] [--tenant TENANT] [--template_only] --dbtype DBTYPE --data_host DATAHOSTS --dbfqdn DBFQDN

Arguments:
  --dbtype DBTYPE           Database type (e.q. mysql, mysql_mha, mssql, mssql_alwayson)
  --dbfqdn DBFQDN           Database FQDN (e.q. FQDN or FQDN:IP)
  --data_host DATAHOSTS     Hosts (e.q. hostname1:ip1,hostname2:ip2 ...)
Options:
  -h --help                 Show this screen.
  --workdir WORKDIR         Working Directory [default: /opt/ansible]
  --sshpass SSHPASS         Ansible ssh password
  --sshport SSHPORT         Ansible ssh port [default: 22]
  --sshkey SSHKEY           Ansible ssh key file [default: /opt/ansible/db.pem]
  --ssh_try_limit SSHLIMIT  test count for ssh reachable (socket timeout is 5 sec) [default: 3]
  --cluster_id CLUSTERID    Cluster id
  --service_name SRVNAME    Service Name
  --tenant TENANT           Tenant Name
  --taskid TASKID           Task id for create mysql single instance
  --template_only           Generate template only
  --minute MINUTE           Crontab minute [default: 2]
  --hour HOUR               Crontab hour [default: 23]
  --day DAY                 Crontab day [default: *]
  --month MONTH             Crontab month [default: *]
  --day_of_week DAYOFWEEK   Crontab day of week [default: *]
  --rsets RSETS             Backup retension sets [default: 3]
  --isets ISETS             Increamental backup in backup retension sets [default: 2]
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
import ara.shell
from StringIO import StringIO
import json

def dbbackup(args, func_type, fields):
    start_time = time.time()
    hosts_script = []
    hosts_script.append('[backup]')
    backup_dict={k[2:]:v for k, v in args.items()}
    if args['--taskid']:
        backup_dict['task_id']='  external_task_id: {}\n'.format(args['--taskid'])
        backup_dict['uuid']=args['--taskid']
    else:
        backup_dict['uuid']=str(uuid.uuid4())
        backup_dict['task_id']='  external_task_id: {}\n'.format(backup_dict['uuid'])
    log_filename=os.path.join(backup_dict['workdir'],'dbbackup_%s_%s_%s.log' % (backup_dict['dbtype'], func_type, backup_dict['uuid']))
    logger = common.MyLogger('dbbackup_%s_%s' % (backup_dict['dbtype'], backup_dict['uuid']), log_filename).default_logger.logger
    logger.info('args:'+str(args))
    backup_dict['data_hosts']=args['--data_host'].split(",")
    backup_dict['ssh_try_limit']=int(args['--ssh_try_limit'])
    playbook_template = 'dbbackup-%s-%s-playbook.j2' % (backup_dict['dbtype'], func_type)
    playbook_filename=os.path.join(backup_dict['workdir'],'dbbackup_%s_%s_%s.yml' % (backup_dict['dbtype'], func_type, backup_dict['uuid']))

    host_filename=os.path.join(backup_dict['workdir'],'inventory',backup_dict['uuid'],'hosts')
    if backup_dict['sshpass']:
        ansible_auth='ansible_ssh_pass={}'.format(backup_dict['sshpass'])
    else:
        ansible_auth='ansible_ssh_private_key_file={}'.format(backup_dict['sshkey'])

    host_list=[]
    ip_list=[]
    for i, host_info in enumerate(backup_dict['data_hosts']):
        (k, v) = host_info.split(":")
        k=k.lower()
        host_list.append(k)
        ip_list.append(v)
        hosts_script.append('{:<60}{:<60}ansible_ssh_port={:<7}{} {}'.format(k, 'ansible_ssh_host='+v, str(backup_dict['sshport']), ansible_auth, backup_dict['hostarg']))

    logger.info('create ansible hosts: {}'.format(host_filename))
    common.render_template('\n'.join(hosts_script),{},host_filename)
    logger.info('craete ansible playbooks: {}'.format(playbook_filename))
    common.render_template('\n'.join(common.read_template(os.path.join(common.template_dir,playbook_template))),backup_dict,playbook_filename)
    if backup_dict['template_only']:
        print('You can run ansible-playbook -i {} {}'.format(host_filename, playbook_filename))
        print("--- Total Excution time: %s ---" % str(timedelta(seconds=(time.time() - start_time))))
    else:
        logger.info('check ssh availability')
        i=1
        check_list = []
        for check_ip in ip_list:
            while (not common.check_server(check_ip,int(backup_dict['sshport']))) and (i < backup_dict['ssh_try_limit']) :
                time.sleep(1)
                i+=1
        for check_ip in ip_list:
            check_result = common.check_server(check_ip,int(backup_dict['sshport']))
            check_list.append(check_result)
            if (not check_result):
                logger.info('ssh check limit exceed ({} sec): ip {}'.format(str(backup_dict['ssh_try_limit']), check_ip))
        logger.info('run ansible from python')
        runner = pyansible.playbooks.Runner(hosts_file=host_filename, playbook_file=playbook_filename, verbosity=3)
        runner.run()
        print("--- Total Excution time: %s ---" % str(timedelta(seconds=(time.time() - start_time))))
        result_dict = {}
        araapi = common.AraApi()

        for i, host_info in enumerate(host_list):
            cmd = 'data show --playbook %s mybak_%s -f json' % (backup_dict['uuid'], host_info)
            result = araapi.run_result(cmd)
            if result['stderr']:
                logger.error('ara cmd error: {}: {}'.format(host_info, result['stderr']))
            if result['stdout']:
                tmp_dict = json.loads(result['stdout'])['Value']
                if isinstance(tmp_dict, list):
                    tmp_dict = {'backup_list': tmp_dict}
            else:
                 tmp_dict = {}
            if fields:
                for k in tmp_dict.keys():
                    if k not in fields:
                        tmp_dict.pop(k)
            tmp_dict['ssh_check']=check_list[i]
            result_dict[host_info]=tmp_dict
    logger.info('return value: %s' % (result_dict))
    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__
    return result_dict

def enable(args):
    fields = []
    fields.append('job_exists')
    fields.append('job_context')
    return json.dumps(dbbackup(args, 'enable', fields))

def disable(args):
    fields = []
    fields.append('job_exists')
    fields.append('job_context')
    return json.dumps(dbbackup(args, 'disable', fields))

def status(args):
    fields = []
    fields.append('job_exists')
    fields.append('job_context')
    return json.dumps(dbbackup(args, 'query', fields))

def listx(args):
    fields = []
    return json.dumps(dbbackup(args, 'list', fields))
