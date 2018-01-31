#!/usr/bin/python

"""
generate ansible inventory for mha

Usage:
  pyansibleinv mha [--monitor_vip MONVIP] [--password PASSWORD] [--workdir WORKDIR] [--sshpass SSHPASS] [--sshkey SSHKEY] [--taskid TASKID] --cluster_id CLUSTERID --data_host DATAHOSTS --monitor_host MONHOSTS --db_vip DBVIP

Arguments:
  --cluster_id CLUSTERID    MySQL mha Cluster id
  --data_host DATAHOSTS     MySQL Hosts for mha (e.q. hostname1:ip1,hostname2:ip2 ...)
  --monitor_host MONHOSTS   Monitor Hosts for mha (e.q. hostname1:ip1,hostname2:ip2 ...)
  --db_vip WVIP             DB vip for mha (e.q. 192.168.10.2)
Options:
  -h --help                 Show this screen.
  --monitor_vip MONVIP      Monitor vip for mha (e.q. 192.168.10.1) [default: 192.168.10.1]
  --database DATABASE       Database name create for mysql [default: db1]
  --password PASSWORD       database password [default: password]
  --workdir WORKDIR         Working Directory [default: /opt/ansible]
  --sshpass SSHPASS         Ansible ssh password
  --sshkey SSHKEY           Ansible ssh key file [default: /opt/ansible/db.pem]
  --taskid TASKID           Task id for create mysql single instance
"""

from docopt import docopt
import common
import os
import pyansible.playbooks
import uuid

def gen_inv(args):
    playbook_template = 'mha-playbook.j2'
    setting_template = 'mha-setting.j2'

    hosts_script = []
    mha_group_script = []
    replication_script = []
    hosts_script.append('[mha]')
    mha_dict = {}
    mha_dict['monitor_vip']=args['--monitor_vip']
    mha_dict['password']=args['--password']
    mha_dict['cluster_id']=args['--cluster_id']
    data_hosts=args['--data_host'].split(",")
    monitor_hosts=args['--monitor_host'].split(",")
    mha_dict['db_vip']=args['--db_vip']
    mha_dict['ssh_pass']=args['--sshpass']
    mha_dict['ssh_key']=args['--sshkey']
    mha_dict['workdir']=args['--workdir']
    if args['--taskid']:
        mha_dict['task_id']='  external_task_id: {}\n'.format(args['--taskid'])
        mha_dict['uuid']=args['--taskid']
    else:
        mha_dict['task_id']=''
        mha_dict['uuid']=str(uuid.uuid4())
    if mha_dict['ssh_pass']:
        ansible_auth='ansible_ssh_pass={}'.format(mha_dict['ssh_pass'])
    else:
        ansible_auth='ansible_ssh_private_key_file={}'.format(mha_dict['ssh_key'])

    playbook_filename=os.path.join(mha_dict['workdir'],'mha_'+ mha_dict['uuid']+'.yml')
    host_filename=os.path.join(mha_dict['workdir'],'inventory',mha_dict['uuid'],'hosts')
    setting_filename=os.path.join(mha_dict['workdir'],'inventory',mha_dict['uuid'],'pillar','mha.yml')

    for i, host_info in enumerate(monitor_hosts):
        (k, v) = host_info.split(":")
        hosts_script.append('{:<30}{:<30}{}'.format(k, 'ansible_ssh_host='+v, ansible_auth))
        mha_group_script.append('      - hostname: {}'.format(k))
        mha_group_script.append('        role: monitor')

    master_host=''
    for i, host_info in enumerate(data_hosts):
        (k, v) = host_info.split(":")
        hosts_script.append('{:<30}{:<30}{}'.format(k, 'ansible_ssh_host='+v, ansible_auth))
        mha_group_script.append('      - hostname: {}'.format(k))
        if i == 0:
            master_host=k
            mha_group_script.append('        role: master')
        else:
            mha_group_script.append('        role: slave')
        mha_group_script.append('        mha_args:')
        mha_group_script.append('          - candidate_master: "1"')
        if i > 0:
            replication_script.append('    {}:'.format(k))
            replication_script.append('      master_host: {}'.format(master_host))


    mha_dict['mha_group']='\n'.join(mha_group_script)
    mha_dict['mysql_replication']='\n'.join(replication_script)
    print('create ansible hosts: {}'.format(host_filename))
    common.render_template('\n'.join(hosts_script),{},host_filename)
    print('craete ansible playbooks: {}'.format(playbook_filename))
    common.render_template('\n'.join(common.read_template(os.path.join(common.template_dir,playbook_template))),mha_dict,playbook_filename)
    print('create mysql with mha setting: {}'.format(setting_filename))
    common.render_template('\n'.join(common.read_template(os.path.join(common.template_dir,setting_template))),mha_dict,setting_filename)
    print('run ansible from python')
    runner = pyansible.playbooks.Runner(hosts_file=host_filename, playbook_file=playbook_filename, verbosity=3)
    runner.run()
    return None