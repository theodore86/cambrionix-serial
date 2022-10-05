""" XML-RPC Server """

import sys
import socket
import argparse
import signal
import threading
from six.moves.xmlrpc_server import SimpleXMLRPCServer
from cambrionix.logger import get_logger


class XMLRPCServer(SimpleXMLRPCServer):

    def __init__(self, host='127.0.0.1', port=8200, logger=None, serve=False):
        """
        Initialize an XML-RPC server.

        :param str host: IPv4 or IPv6 address.
        :param int port: Port number.
        :param Logger: An logger instance.
        :param bool serve: If ``True`` starts the server automatically.
        """
        SimpleXMLRPCServer.__init__(
            self, (host, port), logRequests=False,
            bind_and_activate=False, allow_none=True
        )
        self._activated = False
        self._shutdown_thread = None
        self._logger = logger or get_logger(self.__class__.__name__)
        if serve:
            self.serve()

    @property
    def address(self):
        return self.server_address[0]

    @property
    def port(self):
        return self.server_address[1]

    def activate(self):
        """
        Bind and activate server but
        do not yet start serving.
        """
        if not self._activated:
            self.server_bind()
            self.server_activate()
            self._activated = True
        return self.port

    def serve(self):
        """
        Activate and start the XML-RPC server.
        Upon any of registered signals cleanup the server.

        :returns: Nothing
        """
        self.activate()
        self._announce_start()
        with SignalHandler(self.stop):
            self.serve_forever()
        self.server_close()
        self._wait_server_close()
        self._announce_stop()

    def stop(self):
        """
        Stop the XML-RPC server.

        Create an new daemon thread to shutoff
        the main XML-RPC thread. Thread will be created
        upon any of the register signals.

        :returns: Nothing.
        """
        self._shutdown_thread = threading.Thread(target=self.shutdown)
        self._shutdown_thread.daemon = True
        self._shutdown_thread.start()

    def _wait_server_close(self):
        if self._shutdown_thread:
            self._shutdown_thread.join()  # Wait until daemon thread task ends.
            self._shutdown_thread = None

    def _log(self, action, log=True):
        if log:
            self._logger.info(
                'Server at %s:%s %s', self.address, self.port, action
            )

    def _announce_start(self):
        self._log('started')

    def _announce_stop(self):
        self._log('stopped')


class Ipv6XMLRPCServer(XMLRPCServer):
    """ IPv6 XML-RPC server """

    address_family = socket.AF_INET6

    def __init__(self, host='::1', port=8200, logger=None, serve=False):
        XMLRPCServer.__init__(self,
                              host=host,
                              port=port,
                              logger=logger,
                              serve=serve)


class SignalHandler(object):
    """ An signal handler """

    SIGNALS = ('SIGTERM', 'SIGINT', 'SIGHUP')

    def __init__(self, handler):
        self._handler = lambda signum, frame: handler()
        self._names_to_handler = {}

    def __enter__(self):
        for name in self.__class__.SIGNALS:
            if hasattr(signal, name):
                handler = signal.signal(getattr(signal, name), self._handler)
                self._names_to_handler[name] = handler

    def __exit__(self, exc_type, exc_value, traceback):
        while self._names_to_handler:
            name, handler = self._names_to_handler.popitem()
            signal.signal(getattr(signal, name), handler)


def parse_arguments(argv=None):
    """ Argument parser for XML-RPC server """
    parser = argparse.ArgumentParser(
        description=__doc__,
        usage='python -m tools.xmlrpc [options]'
    )
    parser.add_argument(
        '--rpc-host', dest='rpc_host', type=str,
        help='XML-RPC server IP address', default='127.0.0.1'
    )
    parser.add_argument(
        '--rpc-port', dest='rpc_port', type=int,
        help='XML-RPC server listening port', default=8200
    )
    parser.add_argument(
        '--ipv6', dest='ipv6', action='store_true',
        help='Enable the IPv6 XML-RPC server'
    )
    args = parser.parse_args(argv)
    return args


def main(argv=None, instance=None, logger=None):
    """
    Main IPv4v6 XML-RPC server.

    :param list argv: List of command line arguments.
    :param instance: Register an instance to respond to XML-RPC requests.
    :param Logger: User-defined logger instance, default: ``__main__``.
    :returns int: Exit status, 0 (success) or 1 (failure)
    """
    args = parse_arguments(argv)
    server = Ipv6XMLRPCServer if args.ipv6 else XMLRPCServer
    logger = logger or get_logger(__name__)
    srv = server(args.rpc_host, args.rpc_port)
    try:
        srv.register_introspection_functions()
        srv.register_instance(instance)
        srv.serve()
    except socket.error as e:
        logger.error(e)
        return 1
    else:
        return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
