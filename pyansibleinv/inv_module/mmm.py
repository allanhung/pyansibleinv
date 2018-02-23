#!/usr/bin/python

"""
generate ansible inventory for mmm

Usage:
  pyansibleinv mmm [--monitor_vip MONVIP] [--password PASSWORD] --cluster_id CLUSTERID --data_host DATAHOSTS --monitor_host MONHOSTS --writer_vip WVIP --reader_vip RVIP

Arguments:
  --cluster_id CLUSTERID    MySQL mmm Cluster id
  --data_host DATAHOSTS     MySQL Hosts for mmm (e.q. hostname1:ip1,hostname2:ip2 ...)
  --monitor_host MONHOSTS   Monitor Hosts for mmm (e.q. hostname1:ip1,hostname2:ip2 ...)
  --writer_vip WVIP         Writer vip for mmm (e.q. ip1,ip2 ...)
  --reader_vip RVIP         Reader vip for mmm (e.q. ip1,ip2 ...)
Options:
  -h --help                 Show this screen.
  --monitor_vip MONVIP      Monitor vip for mmm (e.q. ip1,ip2 ...) [default: 192.168.10.1]
  --password PASSWORD       Host password [default: password]
"""

from docopt import docopt
import common
import os

def gen_inv(args):
    log_filename='mmm.log'
    logger = common.MyLogger('mmm', log_filename).default_logger.logger
    playbook_template = 'mmm-playbook.j2'
    setting_template = 'mmm-setting.j2'

    hosts_script = []
    hosts_script.append('[mmm]')
    mmm_dict = {}
    monitor_vips=args['--monitor_vip'].split(",")
    password=args['--password']
    cluster_id=args['--cluster_id']
    data_hosts=args['--data_host'].split(",")
    monitor_hosts=args['--monitor_host'].split(",")
    writer_vips=args['--writer_vip'].split(",")
    reader_vips=args['--reader_vip'].split(",")

    mmm_dict['cluster_id']=cluster_id
    mmm_dict['mon_fqdn']='monitor_vip'
    mmm_dict['mon_vips']=monitor_vips
    mmm_dict['writer_fqdn']='writer_vip'
    mmm_dict['writer_vips']=writer_vips
    mmm_dict['reader_fqdn']='reader_vip'
    mmm_dict['reader_vips']=reader_vips

    for i, host_info in enumerate(monitor_hosts):
        (k, v) = host_info.split(":")
        hosts_script.append('{:<60}{:<60}{}'.format(k, 'ansible_ssh_host='+v, 'ansible_ssh_pass='+password))
        mmm_dict['mon_host'+str(i+1)]=k

    for i, host_info in enumerate(data_hosts):
        (k, v) = host_info.split(":")
        hosts_script.append('{:<60}{:<60}{}'.format(k, 'ansible_ssh_host='+v, 'ansible_ssh_pass='+password))
        mmm_dict['data_host'+str(i+1)]=k

    logger.info('ansible hosts:\n')
    logger.info('\n'.join(hosts_script)+'\n')
    logger.info('ansible playbooks:\n')
    logger.info(common.render_template('\n'.join(common.read_template(os.path.join(common.template_dir,playbook_template))),{},'')+'\n')
    logger.info('mmm setting:\n')
    logger.info(common.render_template('\n'.join(common.read_template(os.path.join(common.template_dir,setting_template))),mmm_dict,'')+'\n')
    return None
