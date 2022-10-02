"""
Cambrionix XML-RPC server.
Server is build on top of XMLRPCServer.

Exposes the Cambrionix serial API through XML-RPC.
"""

import sys
import argparse
from cambrionix import Cambrionix
from cambrionix.logger import get_logger
from .xmlrpc import main as _main


LOGGER = get_logger(__name__)


def main(argv=None, logger=None):
    logger = logger or get_logger(__name__)
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawTextHelpFormatter,
        usage='python -m cambrionix.tools.cbrxxmlrpc [options]'
    )
    parser.add_argument(
        '--serial-port', dest='port',
        type=str, required=True,
        help='Cambrionix serial port name'
    )
    parser.add_argument(
        '--serial-timeout', dest='timeout',
        type=int, default=15.0,
        help='Cambrionix serial read timeout'
    )
    args, rest = parser.parse_known_args(argv)
    try:
        cbrx = Cambrionix(args.port, timeout=args.timeout)
    except ValueError as e:
        LOGGER.error(e)
        return 1
    return _main(
        rest, instance=cbrx, logger=logger
    )


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:], logger=LOGGER))
