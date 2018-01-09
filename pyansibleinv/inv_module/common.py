#!/usr/bin/python

import os
import pyansibleinv
from jinja2 import Template

template_dir = '/usr/share/pyansibleinv'

def render_template(template_str, template_dict, output_file):
    output_str = Template(template_str).render(template_dict) if template_dict else template_str
    # to save the results
    if output_file:
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
