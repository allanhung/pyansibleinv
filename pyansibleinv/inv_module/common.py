#!/usr/bin/python

import os
import sys
import socket
import pyansibleinv
import logging
from jinja2 import Template
from datetime import datetime

template_dir = '/usr/share/pyansibleinv'

class MyFormatter(logging.Formatter):
    converter=datetime.fromtimestamp
    def formatTime(self, record, datefmt=None):
        ct = self.converter(record.created)
        if datefmt:
            s = ct.strftime(datefmt)
        else:
            t = ct.strftime("%Y-%m-%d %H:%M:%S")
            s = "%s.%03d" % (t, record.msecs)
        return s

class StreamToLogger(object):
   """
   Fake file-like stream object that redirects writes to a logger instance.
   """
   def __init__(self, module, log_file, log_level, log_format, log_date_format):
      self.logger = logging.getLogger(module)
      self.set_log_level(log_level)
      self.formatter = MyFormatter(log_format, log_date_format)
      self.fh = logging.FileHandler(log_file)
      self.fh.setFormatter(self.formatter)
      self.logger.addHandler(self.fh)
      self.linebuf = ''

   def set_log_level(self, log_level):
      self.log_level = log_level
      self.logger.setLevel(log_level)

   def write(self, buf):
      for line in buf.rstrip().splitlines():
         self.logger.log(self.log_level, line.rstrip())

   def flush(self):
      # do notthing for flush
      pass

class MyLogger(object):
   def __init__(self, module, log_file, log_level=logging.INFO, log_format='%(asctime)s - %(name)s - %(levelname)5s - %(message)s', log_date_format=None):
      name_length=str(len(module)+len('stdout')+1)
      log_format=log_format.replace('%(name)s','%(name)'+name_length+'s')     
      self.default_logger = StreamToLogger(module, log_file, log_level, log_format, log_date_format)
      self.stdout_logger = StreamToLogger(module+'_stdout', log_file, logging.INFO, log_format, log_date_format)
      sys.stdout = self.stdout_logger
      self.stderr_logger = StreamToLogger(module+'_stderr', log_file, logging.ERROR, log_format, log_date_format)
      sys.stderr = self.stderr_logger

def check_server(address, port):
    # Create a TCP socket
    s = socket.socket()
    print "Attempting to connect to %s on port %s" % (address, port)
    try:
        s.connect((address, port))
        print "Connected to %s on port %s" % (address, port)
        return True
    except socket.error, e:
        print "Connection to %s on port %s failed: %s" % (address, port, e)
        return False

def render_template(template_str, template_dict, output_file):
    output_str = Template(template_str).render(template_dict) if template_dict else template_str
    # to save the results
    if output_file:
        directory = os.path.dirname(output_file)
        if not os.path.exists(directory):
            os.makedirs(directory)
        with open(output_file, "wb") as f:
            f.write(output_str+'\n')
    else:
        return output_str

def read_template(filename):
    result=[]
    with open(filename, 'r') as f:
        result = f.read().splitlines()
    return result

def convertUnicodeToString(data):
    if isinstance(data, basestring):
        return str(data)
    elif isinstance(data, collections.Mapping):
        return dict(map(convertUnicodeToString, data.iteritems()))
    elif isinstance(data, collections.Iterable):
        return type(data)(map(convertUnicodeToString, data))
    else:
        return data
