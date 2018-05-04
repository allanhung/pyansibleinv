#!/usr/bin/python

"""
generate ansible inventory for mmm

Usage:
  pyansibleinv mmm [--monitor_vip MONVIP] [--password PASSWORD] [--workdir WORKDIR] [--sshpass SSHPASS] [--sshkey SSHKEY] [--ssh_try_limit SSHLIMIT] [--taskid TASKID] --cluster_id CLUSTERID --data_host DATAHOSTS --monitor_host MONHOSTS --writer_vip WVIP --reader_vip RVIP

Arguments:
  --cluster_id CLUSTERID    MySQL mmm Cluster id
  --data_host DATAHOSTS     MySQL Hosts for mmm (e.q. hostname1:ip1,hostname2:ip2 ...)
  --monitor_host MONHOSTS   Monitor Hosts for mmm (e.q. hostname1:ip1,hostname2:ip2 ...)
  --writer_vip WVIP         Writer vip for mmm (e.q. ip1,ip2 ...)
  --reader_vip RVIP         Reader vip for mmm (e.q. ip1,ip2 ...)
Options:
  -h --help                 Show this screen.
  --monitor_vip MONVIP      Monitor vip for mmm (e.q. ip) [default: 192.168.10.1]
  --password PASSWORD       Host password [default: password]
  --workdir WORKDIR         Working Directory [default: /opt/ansible]
  --sshpass SSHPASS         Ansible ssh password
  --sshkey SSHKEY           Ansible ssh key file [default: /opt/ansible/db.pem]
  --ssh_try_limit SSHLIMIT  test count for ssh reachable (socket timeout is 5 sec) [default: 120]
"""

from docopt import docopt
import common
import os
import time
from datetime import timedelta
import uuid

def gen_inv(args):
    start_time = time.time()
    log_filename='mmm.log'
    logger = common.MyLogger('mmm', log_filename).default_logger.logger
    logger.info('args:'+str(args))
    playbook_template = 'mmm-playbook.j2'
    setting_template = 'mmm-setting.j2'

    hosts_script = []
    hosts_script.append('[mmm]')
    mmm_dict={k[2:]:v for k, v in args.items()}
    mmm_dict['mon_fqdn']='monitor_vip'
    mmm_dict['heartbeat']='' if mmm_dict['monitor_vip'] == '192.168.10.1' else '\n    - heartbeat'
    mmm_dict['writer_fqdn']='writer_vip'
    mmm_dict['writer_vips']=args['--writer_vip'].split(",")
    mmm_dict['reader_fqdn']='reader_vip'
    mmm_dict['reader_vips']=args['--reader_vip'].split(",")
    mmm_dict['monitor_hosts']=args['--monitor_host'].split(",")
    if len( mmm_dict['monitor_hosts']) == 1:
         mmm_dict['monitor_hosts'].append('fakehost.domain:192.168.98.98')
    mmm_dict['data_hosts']=args['--data_host'].split(",")
    mmm_dict['ssh_try_limit']=int(args['--ssh_try_limit'])
    if args['--taskid']:
        mmm_dict['task_id']='  external_task_id: {}\n'.format(args['--taskid'])
        mmm_dict['uuid']=args['--taskid']
    else:
        mmm_dict['task_id']=''
        mmm_dict['uuid']=str(uuid.uuid4())
    if mmm_dict['sshpass']:
        ansible_auth='ansible_ssh_pass={}'.format(mmm_dict['sshpass'])
    else:
        ansible_auth='ansible_ssh_private_key_file={}'.format(mmm_dict['sshkey'])

    playbook_filename=os.path.join(mmm_dict['workdir'],'mmm_'+ mmm_dict['uuid']+'.yml')
    host_filename=os.path.join(mmm_dict['workdir'],'inventory',mmm_dict['uuid'],'hosts')
    setting_filename=os.path.join(mmm_dict['workdir'],'inventory',mmm_dict['uuid'],'pillar','mmm.yml')

    mmm_dict['data_hostlist']=[]
    mmm_dict['mmm_hostlist']=[]
    for i, host_info in enumerate(mmm_dict['monitor_hosts']):
        (k, v) = host_info.split(":")
        k=k.lower()
        mmm_dict['mmm_hostlist'].append(k)
        hosts_script.append('{:<60}{:<60}{}'.format(k, 'ansible_ssh_host='+v, ansible_auth))
        mmm_dict['mon_host'+str(i+1)]=k

    for i, host_info in enumerate(mmm_dict['data_hosts']):
        (k, v) = host_info.split(":")
        k=k.lower()
        mmm_dict['data_hostlist'].append(k)
        hosts_script.append('{:<60}{:<60}{}'.format(k, 'ansible_ssh_host='+v, ansible_auth))
        mmm_dict['data_host'+str(i+1)]=k

    logger.info('create ansible hosts: {}'.format(host_filename))
    common.render_template('\n'.join(hosts_script),{},host_filename)
    logger.info('craete ansible playbooks: {}'.format(playbook_filename))
    common.render_template('\n'.join(common.read_template(os.path.join(common.template_dir,playbook_template))),mmm_dict,playbook_filename)
    logger.info('create mysql with mmm setting: {}'.format(setting_filename))
    common.render_template('\n'.join(common.read_template(os.path.join(common.template_dir,setting_template))),mmm_dict,setting_filename)
    print('You can run ansible-playbook -i {} {}'.format(host_filename, playbook_filename))
    print("--- Total Excution time: %s ---" % str(timedelta(seconds=(time.time() - start_time))))
    print('You can connect db with:\n    mysql -uroot -p{} -h{}'.format(mmm_dict['password'],mmm_dict['writer_vips'][0]))
    return None
