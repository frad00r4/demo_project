# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

import os
import sys
import ujson

from demo.main import runner


def main():
    if len(sys.argv) < 2:
        return 2

    dir_path = os.path.dirname(os.path.realpath(__file__))
    try:
        with open('%s/configs/%s.json' % (dir_path, sys.argv[1]), 'r') as fd:
            conf = ujson.load(fd)
            return runner(conf)
    except IOError as e:
        print('ERROR: config file error')
        print(e)
    except ValueError as e:
        print('ERROR: config parsing error')
        print(e)

    return 1


"""
returns codes
0 - normal exit
1 - error with config load/parse
2 - config doesn't set
3 - config issues
"""
if __name__ == '__main__':
    sys.exit(main())
