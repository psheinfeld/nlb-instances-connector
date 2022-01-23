import logging

# create log
log = logging.getLogger('k8sLabeler')
log.setLevel(logging.INFO)

# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

# create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%m/%d/%Y %H:%M:%S')

# add formatter to ch
ch.setFormatter(formatter)

# add ch to log
log.addHandler(ch)

# 'application' code
log.debug('debug message')
log.info('info message')
log.warning('warn message')
log.error('error message')
log.critical('critical message')