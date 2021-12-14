import logging
import logging.config
import logging.handlers
import os.path
from sys import executable


def ConfigLogger():
    exe_path = os.path.dirname(executable)

    LOGGING_CONFIG = {
        'version': 1,
        'disable_existing_loggers': True,
        'formatters': {
            'standard': {
                'format': '%(asctime)s [%(levelname)-8s] : %(message)s'
            },
        },
        'handlers': {
            'default_handler': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'DEBUG',
                'formatter': 'standard',
                'filename': os.path.join(exe_path, 'ASIS_Disk_Health_Monitor.log'),
                'encoding': 'utf8',
                'mode': 'a',
                'maxBytes': 10485760,
                'backupCount': 10,
            }
        },
        'loggers': {
            '': {
                'handlers': ['default_handler'],
                'level': 'NOTSET',
                'propagate': False,
            }
        }
    }
    logging.config.dictConfig(LOGGING_CONFIG)


if __name__ == "__main__":
    ConfigLogger()
    logger = logging.getLogger(__name__)
    logger.debug('debug log')
    logger.info('info log')
    logger.warning('warning log')
    logger.error('error log')
    logger.critical('critical log')
    logger.exception('exception log')
