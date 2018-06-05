#!/usr/bin/python

"""
generate ansible inventory for pxc

Usage:
  pyansibleinv pxc [--monitor_vip MONVIP] [--password PASSWORD] [--workdir WORKDIR] [--sshpass SSHPASS] [--sshport SSHPORT] [--sshkey SSHKEY] [--hostarg HOSTARG] [--ssh_try_limit SSHLIMIT] [--taskid TASKID] [--cluster_id CLUSTERID] [--service_name SRVNAME] [--tenant TENANT] [--template_only] [--without_parted] [--without_backup] [--monitor_host MONHOSTS] [--db_vip DBVIP] --data_host DATAHOSTS

Arguments:
  --data_host DATAHOSTS     MySQL Hosts for pxc (e.q. hostname1:ip1,hostname2:ip2 ...)
Options:
  -h --help                 Show this screen.
  --monitor_vip MONVIP      Monitor vip for pxc (e.q. 192.168.10.1) [default: 192.168.10.1]
  --monitor_host MONHOSTS   Monitor Hosts for pxc (e.q. hostname1:ip1,hostname2:ip2 ...)
  --db_vip WVIP             DB vip for pxc (e.q. 192.168.10.2)
  --database DATABASE       Database name create for mysql [default: db1]
  --password PASSWORD       database password [default: password]
  --workdir WORKDIR         Working Directory [default: /opt/ansible]
  --sshpass SSHPASS         Ansible ssh password
  --sshport SSHPORT         Ansible ssh port [default: 22]
  --sshkey SSHKEY           Ansible ssh key file [default: /opt/ansible/db.pem]
  --hostarg HOSTARG         Ansible hosts additional arguments
  --ssh_try_limit SSHLIMIT  test count for ssh reachable (socket timeout is 5 sec) [default: 120]
  --cluster_id CLUSTERID    Cluster id
  --service_name SRVNAME    Service Name
  --tenant TENANT           Tenant Name
  --taskid TASKID           Task id for create mysql single instance
  --template_only           Generate template only
  --without_parted          without partition and format disk
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
    playbook_template = 'pxc-playbook.j2'
    setting_template = 'pxc-setting.j2'

    ip_list = []
    hosts_script = []
    pxc_group_script = []
    hosts_script.append('[pxc]')
    pxc_dict={k[2:]:v for k, v in args.items()}
    pxc_dict['data_hosts']=args['--data_host'].split(",")
    if args['--monitor_host']:
        pxc_dict['monitor_hosts']=args['--monitor_host'].split(",")
    else:
        pxc_dict['monitor_hosts']=[]
    pxc_dict['ssh_try_limit']=int(args['--ssh_try_limit'])
    if args['--taskid']:
        pxc_dict['task_id']='  external_task_id: {}\n'.format(args['--taskid'])
        pxc_dict['uuid']=args['--taskid']
    else:
        pxc_dict['task_id']=''
        pxc_dict['uuid']=str(uuid.uuid4())

    pxc_dict['parted']='' if args['--without_parted'] else '\n    - parted'
    pxc_dict['enable_backup']=not args['--without_backup']

    if pxc_dict['sshpass']:
        ansible_auth='ansible_ssh_pass={}'.format(pxc_dict['sshpass'])
    else:
        ansible_auth='ansible_ssh_private_key_file={}'.format(pxc_dict['sshkey'])
    log_filename=os.path.join(pxc_dict['workdir'],'pxc_'+ pxc_dict['uuid']+'.log')
    logger = common.MyLogger('pxc', log_filename).default_logger.logger
    logger.info('args:'+str(args))
    playbook_filename=os.path.join(pxc_dict['workdir'],'pxc_'+ pxc_dict['uuid']+'.yml')
    host_filename=os.path.join(pxc_dict['workdir'],'inventory',pxc_dict['uuid'],'hosts')
    setting_filename=os.path.join(pxc_dict['workdir'],'inventory',pxc_dict['uuid'],'pillar','pxc.yml')

    pxc_dict['data_hostlist']=[]
    pxc_dict['data_iplist']=[]
    pxc_dict['mon_hostlist']=[]
    for i, host_info in enumerate(pxc_dict['monitor_hosts']):
        (k, v) = host_info.split(":")
        k=k.lower()
        pxc_dict['mon_hostlist'].append(k)
        ip_list.append(v)
        hosts_script.append('{:<60}{:<60}ansible_ssh_port={:<7}{} {}'.format(k, 'ansible_ssh_host='+v, str(pxc_dict['sshport']), ansible_auth, pxc_dict['hostarg']))
        pxc_group_script.append('      - hostname: {}'.format(k))
        pxc_group_script.append('        role: arbitrator')
        pxc_group_script.append('        bootstrap: False')
        if pxc_dict['db_vip']:
            pxc_group_script.append('        vip: {}'.format(pxc_dict['db_vip']))

    for i, host_info in enumerate(pxc_dict['data_hosts']):
        (k, v) = host_info.split(":")
        k=k.lower()
        pxc_dict['data_hostlist'].append(k)
        pxc_dict['data_iplist'].append(v)
        hosts_script.append('{:<60}{:<60}ansible_ssh_port={:<7}{} {}'.format(k, 'ansible_ssh_host='+v, str(pxc_dict['sshport']), ansible_auth, pxc_dict['hostarg']))
        ip_list.append(v)
        pxc_group_script.append('      - hostname: {}'.format(k))
        pxc_group_script.append('        role: data')
        if i == 0:
            pxc_group_script.append('        bootstrap: True')
        else:
            pxc_group_script.append('        bootstrap: False')

    if pxc_dict['db_vip']:
        pxc_dict['ha_setting']="\n    - pacemaker\n    - lvs"
    pxc_dict['pxc_group']='\n'.join(pxc_group_script)
    logger.info('create ansible hosts: {}'.format(host_filename))
    common.render_template('\n'.join(hosts_script),{},host_filename)
    logger.info('craete ansible playbooks: {}'.format(playbook_filename))
    common.render_template('\n'.join(common.read_template(os.path.join(common.template_dir,playbook_template))),pxc_dict,playbook_filename)
    logger.info('create mysql with pxc setting: {}'.format(setting_filename))
    common.render_template('\n'.join(common.read_template(os.path.join(common.template_dir,setting_template))),pxc_dict,setting_filename)
    if pxc_dict['template_only']:
        print('You can run ansible-playbook -i {} {}'.format(host_filename, playbook_filename))
    else:
        logger.info('check ssh availability')
        i=1
        for check_ip in ip_list:
            while (not common.check_server(check_ip,int(pxc_dict['sshport']))) and (i < pxc_dict['ssh_try_limit']) :
                time.sleep(1)
                i+=1
        for check_ip in ip_list:
            if (not common.check_server(check_ip,int(pxc_dict['sshport']))):
                logger.info('ssh check limit exceed ({} sec): ip {}'.format(str(pxc_dict['ssh_try_limit']), check_ip))
        logger.info('run ansible from python')
        runner = pyansible.playbooks.Runner(hosts_file=host_filename, playbook_file=playbook_filename, verbosity=3)
        runner.run()
        print("--- Total Excution time: %s ---" % str(timedelta(seconds=(time.time() - start_time))))
        print('You can connect db with:\n    mysql -uroot -p{} -h{} {}'.format(pxc_dict['password'],pxc_dict['ip'],pxc_dict['database']))
    return None
