#!/usr/bin/python

"""pyansibleinv

generate ansible inventory

Usage:
  pyansibleinv <module> <func> [<args>...]

Options:
  -h --help            Show this screen.
"""

from docopt import docopt
import sys
import inv_module
from inv_module import *

def main():
    """
    run module

    example:
    pyansibleinv mmm '{"key1": "value1"}
    """
    args = docopt(__doc__, options_first=True)
    module = args['<module>']
    func = args['<func>']
    argv = [module, func]+args['<args>']
    module_script = getattr(inv_module, module)
    module_args = docopt(module_script.__doc__, argv=argv)
    return getattr(module_script, 'gen_inv')(module_args)

if __name__ == '__main__':
    main()
