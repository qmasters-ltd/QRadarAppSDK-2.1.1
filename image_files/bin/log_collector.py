#!/usr/bin/env python3

'''QRadar App Log Collector'''

import argparse
import os
import signal
import time
import logging
import sys

class AppLogCollector():
    LOGGER_NAME = 'QRadarAppLog'
    LOG_SUFFIXES = ('.log', '.error')

    STDOUT_FORMAT = 'logfile={0}: {1}'
    SYSLOG_FORMAT = '%(message)s'
    LEEF_TEMPLATE = 'LEEF:1.0|QRadar|QRadarAppLogger|1.0|QRadarAppLog|APP_ID={0} LOG_FILE={1} LOG_MESSAGE={2}'

    STRATEGY_STDOUT = 'stdout'
    STRATEGY_SYSLOG = 'syslog'
    STRATEGIES = (STRATEGY_STDOUT, STRATEGY_SYSLOG)

    APP_ID = os.getenv('QRADAR_APP_ID', '0')

    def __init__(self):
        self.running = False
        self.directory = None
        self.strategy = self.STRATEGY_SYSLOG
        self.log_files = {}
        self.logger = None

    def boot(self):
        self.parse_args()
        if self.strategy == self.STRATEGY_SYSLOG:
            self.create_logger()
        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGQUIT, self.shutdown)
        self.run()

    # pylint: disable=unused-argument
    def shutdown(self, signal_number, frame):
        self.running = False

    def parse_args(self):
        log_dir = os.path.join(os.getenv('APP_ROOT'), 'store', 'log')
        parser = argparse.ArgumentParser(description='QRadar App Log Collector')
        parser.add_argument('-d', '--directory', default=log_dir,
                            help='Directory to collect logs from. Defaults to {0}'.format(log_dir))
        parser.add_argument('-l', '--log-strategy', dest='strategy', default='syslog',
                            help='Logging strategy to use. Possible values: syslog (default), stdout')

        args = parser.parse_args()

        if not os.path.isdir(args.directory):
            print('Directory {} does not exist'.format(args.directory))
            sys.exit(1)

        if not args.strategy in self.STRATEGIES:
            print('{} is not a valid log strategy'.format(args.strategy))
            sys.exit(1)

        self.directory = args.directory
        self.strategy = args.strategy

    def run(self):
        self.running = True
        while self.running:
            log_file_paths = self.find_log_files()
            for path in log_file_paths:
                if path not in self.log_files:
                    self.start_handling_log_file(path)
            time.sleep(60)

    def find_log_files(self):
        log_file_paths = []
        # Python3: use pathlib.Path.rglob() instead of os.walk?
        for _, _, files in os.walk(self.directory):
            for log_file_path in files:
                if log_file_path.endswith(self.LOG_SUFFIXES):
                    log_file_paths.append(os.path.join(self.directory, log_file_path))
        return log_file_paths

    def start_handling_log_file(self, log_file_path):
        log_files_entry = {}
        self.log_files[log_file_path] = log_files_entry
        # Start new thread.
        # Send logs based on self.strategy.
        # Populate log_files_entry.
        # Need to handle rotating logs, container stop/start.

    def send_logs_to_stdout(self, log_file_path):
        with open(log_file_path, encoding='utf-8') as log_file:
            for line in log_file:
                print(self.STDOUT_FORMAT.format(log_file_path, line.rstrip()))

    def send_logs_to_syslog(self, log_file_path):
        log_file_basename = os.path.basename(log_file_path)
        with open(log_file_path, encoding='utf-8') as log_file:
            for line in log_file:
                self.log(line.rstrip(), log_file_basename)

    def create_logger(self):
        syslog_handler = logging.handlers.SysLogHandler(address=(os.getenv('QRADAR_CONSOLE_FQDN'), 514))
        syslog_handler.setFormatter(logging.Formatter(self.SYSLOG_FORMAT))
        self.logger = logging.getLogger(self.LOGGER_NAME)
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(syslog_handler)
        self.log('Created log ' + self.LOGGER_NAME, 'log_collector.py')

    def log(self, message, log_file):
        # For now, log every message as INFO.
        log_message = self.LEEF_TEMPLATE.format(self.APP_ID, log_file, message)
        self.logger.info(log_message)

if __name__ == '__main__':
    AppLogCollector().boot()
