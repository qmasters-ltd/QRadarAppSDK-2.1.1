# Licensed Materials - Property of IBM
# 5725I71-CC011829
# (C) Copyright IBM Corp. 2015, 2020. All Rights Reserved.
# US Government Users Restricted Rights - Use, duplication or
# disclosure restricted by GSA ADP Schedule Contract with IBM Corp.

import getpass
import logging
import os
import sys
import paramiko
import socket
import socks
from sdk_progressbar import ProgressBar
from sdk_exceptions import SdkServerConnectionError, SdkServerRequestError

# paramiko outputs all of its errors to system out, so set its log level
# to CRITICAL to prevent it polluting SDK output
logging.getLogger('paramiko').setLevel(logging.CRITICAL)

class SdkSshClient():
    def __init__(self, host, server_config):
        self.host = host
        self.config = server_config
        try:
            self.ssh_client = self._create_ssh_client()
        except OSError as oe:
            raise SdkServerConnectionError('Unable to create ssh client: {0}'.format(oe))

    @staticmethod
    def _create_ssh_client():
        ''' Raises OSError (IOError) '''
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.load_system_host_keys()
        return client

    def connect(self):
        while True:
            try:
                sock = self._open_socket()
                self._connect_with_password(sock)
                break
            except paramiko.AuthenticationException:
                print('Authentication failed. Please check user ID and password and try again')
                sys.stdout.flush()
                sock.close()
            except (socket.error, socks.ProxyError, paramiko.SSHException) as se:
                raise SdkServerConnectionError('Unable to connect to host {0}: {1}'.format(self.host, se))

    def _open_socket(self):
        ''' Raises socket.error, socks.ProxyError '''
        sock = socks.socksocket()
        sock.settimeout(int(os.getenv('SDK_SOCKET_TIMEOUT', '20')))
        if self.config.has_socks_proxy():
            sock.setproxy(self.config.get_socks_protocol(),
                          self.config.get_socks_proxy_host(),
                          port=self.config.get_socks_proxy_port())
        sock.connect((self.host, 22))
        return sock

    def _connect_with_password(self, sock):
        ''' Raises socket.error, paramiko.SSHException '''
        password = getpass.getpass('Enter {0} password for user {1}: '
                                   .format(self.host, self.config.get_server_user_id()))
        self.ssh_client.connect(hostname=self.host,
                                username=self.config.get_server_user_id(),
                                password=password,
                                sock=sock,
                                timeout=int(os.getenv('SDK_SSH_CLIENT_TIMEOUT', '20')),
                                allow_agent=False,
                                look_for_keys=False)

    def close(self):
        self.ssh_client.close()

    def retrieve_server_hostname(self):
        try:
            return self._execute_myver_over_ssh()
        except (paramiko.SSHException, SdkServerRequestError) as se:
            print(('WARNING: Unable to retrieve hostname for {0}. '
                   'Subsequent certificate validation may fail. Reason: {1}').format(self.host, se))
            return None

    def _execute_myver_over_ssh(self):
        ''' Raises paramiko.SSHException, SdkServerRequestError '''
        _, stdout, stderr = self.ssh_client.exec_command('/opt/qradar/bin/myver -vh')
        exit_status = stdout.channel.recv_exit_status()
        if exit_status != 0:
            raise SdkServerRequestError(stderr.read().decode().strip())
        return stdout.read().decode().strip()

    def transfer_ca_cert_bundle(self, destination_path):
        sftp_client = None
        try:
            sftp_client = self._create_sftp_client()
            self._sftp_get_cert_bundle(sftp_client, destination_path)
        except (OSError, paramiko.SSHException) as se:
            raise SdkServerConnectionError('Unable to retrieve CA certificate bundle from host {0}: {1}'
                                           .format(self.host, se))
        finally:
            if sftp_client:
                sftp_client.close()

    def _create_sftp_client(self):
        ''' Raises paramiko.SSHException '''
        return self.ssh_client.open_sftp()

    @staticmethod
    def _sftp_get_cert_bundle(sftp_client, destination_path):
        ''' Raises OSError (IOError) '''
        with ProgressBar(ascii=True, unit='b', unit_scale=True) as progress_bar:
            sftp_client.get('/etc/pki/tls/certs/ca-bundle.crt', destination_path,
                            callback=progress_bar.progress)
