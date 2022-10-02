#!/usr/bin/env python
"""
Module to handle the Cambrionix USB port charging mode.

Supports the Universal Chargers series:

* PPxx
* Uxx
* Thundersync

"""

import sys
import argparse
from cambrionix import Cambrionix
from cambrionix.exceptions import (
    GenericError, FatalError,
    ConfigurationError,
    ConfigurationSectionError
)
from cambrionix.logger import get_logger


LOGGER = get_logger(__name__)


def _split_ports(ports, sep=','):
    uniq = {int(p) for p in ports.split(sep)}
    return sorted(uniq)


def parse_arguments(argv=None):
    """ Parse command line arguments """
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        '--host', dest='host', type=str, required=True,
        help='Hostname of the machine where Cambrionix is integrated.'
    )
    parser.add_argument(
        '--usb-ports', dest='ports', type=_split_ports, required=False,
        default=None, help='Comma separated USB port numbers, Default to: all USB ports.'
    )
    parser.add_argument(
        '--charge-mode', dest='mode', required=False,
        choices=['C', 'CHARGED', 'B', 'BIASED', 'O', 'OFF', 'S', 'SYNC'], default='S',
        help='Port charge mode: (C)harged, (B)iased, (O)FF, (S)ync, Default: (S)ync'
    )
    parser.add_argument(
        '--serial-config', dest='serial_config', type=str, required=True,
        default=None, help='INI configuration file, absolute or relative path.'
    )
    parser.add_argument(
        '--system', dest='system', action='store_true', required=False,
        default=None, help='Display hardware and firmware information'
    )
    parser.add_argument(
        '--health', dest='health', action='store_true', required=False,
        default=None, help='Show voltages, temperature, errors and boot flag'
    )
    args = parser.parse_args(argv)
    return args


def main(argv=None, logger=None):
    args = parse_arguments(argv)
    logger = logger or get_logger(__name__)
    try:
        cbrx = Cambrionix.from_ini(args.host, args.serial_config)
    except (ConfigurationError, ConfigurationSectionError) as e:
        logger.error(e)
        return 1
    except ValueError as e:
        logger.error(e)
        return 1
    with cbrx as c:
        try:
            console = []
            if args.system is not None:
                console.append(c.system)
            if args.health is not None:
                console.append(c.health)
            if args.ports is not None:
                for p in args.ports:
                    c.set_mode(args.mode, p)
                    console.append(c.show_state(p))
            else:
                c.set_mode(args.mode, args.ports)
                console.append(c.show_state(args.ports))
            logger.info('\n%s', '\n\n'.join(console))
        except (GenericError, FatalError) as e:
            logger.error(e)
            return 1
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:], logger=LOGGER))
