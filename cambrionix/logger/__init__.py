import os
import logging
import logging.config
import yaml


__all__ = ['get_logger']


def get_logger(name, cfg_path='logging.yaml'):
    """
    Setup an logger instance.

    .. note::

        Logging instances are **sigleton**. Calling this function
        with the same name will always result with the same logger.

    :param str name: Name of the logger, module or class name.
    :param str cfg_path: Logging configuration file path.
    :returns: an ``Logger`` instance.
    """
    if not os.path.exists(cfg_path):
        cfg_path = os.path.join(
            os.path.dirname(__file__),
            'logging.yaml'
        )
    with open(cfg_path, 'r') as stream:
        config = yaml.safe_load(stream)
    logging.config.dictConfig(config)
    logger = logging.getLogger(name)
    return logger
