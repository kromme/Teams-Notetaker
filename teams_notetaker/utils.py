import subprocess
import logging
import logging.config


def get_logger(name, logfile='log.log'):
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(
        level=logging.DEBUG, format=log_format, filename=logfile, filemode="w"
    )
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    console.setFormatter(logging.Formatter(log_format))
    logging.getLogger(name).addHandler(console)
    return logging.getLogger(name)


logger = get_logger('utils')


def check_cmd_application_available(application: str) -> bool:
    """Check whether a command line interface application is available.

    Parameters
    ----------
    application : str
        Name of the application
    """
    output = subprocess.run(application, shell=True, capture_output=True)
    if 'not recognized' not in str(output.stderr):
        logger.info(f'{application} available.')
        return True
    else:
        logger.error(f'{application} not available')
        return False
