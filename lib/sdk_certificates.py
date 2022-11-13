# Licensed Materials - Property of IBM
# 5725I71-CC011829
# (C) Copyright IBM Corp. 2015, 2020. All Rights Reserved.
# US Government Users Restricted Rights - Use, duplication or
# disclosure restricted by GSA ADP Schedule Contract with IBM Corp.

import os
import sys
import click
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from sdk_serverconfig import ServerConfig
import sdk_sshclient
import sdk_util
from sdk_exceptions import SdkCertError

SDK_CERT_FILE = 'ca-bundle.crt'
MSG_CERT_DOWNLOAD = ('No certificate bundle found for host {0}\n'
                     'You can use the qapp server action to download the certificate bundle')
MSG_CERT_REFRESH = ('Invalid certificate bundle found for host {0}\n'
                    'You can use the qapp server action to refresh the certificate bundle')

def build_cert_bundle_file_path(host):
    return sdk_util.build_config_path(host, SDK_CERT_FILE)

def verify_certificate_bundle(host):
    ''' Possible scenarios:
        - Bundle does not exist, first use: create new bundle.
        - Bundle is valid: nothing to be done.
        - Bundle cannot be loaded: remove it here, then create new bundle.
    '''
    if sdk_util.env_var_is_true('SDK_DISABLE_SECURITY'):
        return False

    cert_bundle_path = build_cert_bundle_file_path(host)
    need_new_bundle = False
    bundle_removed = False

    try:
        validate_existing_bundle(cert_bundle_path)
    except FileNotFoundError:
        need_new_bundle = True
    except SdkCertError:
        print('Removing invalid certificate bundle {0}'.format(cert_bundle_path))
        sys.stdout.flush()
        sdk_util.remove_host_config(host)
        need_new_bundle = True
        bundle_removed = True

    if need_new_bundle:
        print_cert_prompt_header(host, bundle_removed)
        resolve_bundle(host)

    return cert_bundle_path

def check_host_bundle_status(host):
    try:
        validate_existing_bundle(build_cert_bundle_file_path(host))
    except FileNotFoundError:
        raise SdkCertError(MSG_CERT_DOWNLOAD.format(host))
    except SdkCertError:
        raise SdkCertError(MSG_CERT_REFRESH.format(host))

def validate_existing_bundle(cert_bundle_path):
    if not os.path.isfile(cert_bundle_path):
        raise FileNotFoundError('Cert bundle not found')

    try:
        with open(cert_bundle_path) as cert_bundle:
            bundle_pem_text = cert_bundle.read()
            x509.load_pem_x509_certificate(bundle_pem_text.encode(), default_backend())
    except ValueError:
        raise SdkCertError('Bad cert bundle')

def resolve_bundle(host):
    server_config = prompt_server_configuration()
    download_data_from_server(host, server_config)
    server_config.save(host)
    print('Server configuration for {0} saved to {1}'.format(host, ServerConfig.build_config_json_path(host)))
    sys.stdout.flush()

def print_cert_prompt_header(host, bundle_removed):
    # These print statements are in a separate function to facilitate unit testing.
    if not bundle_removed:
        print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
        print('No CA certificate bundle found for {0}'.format(host))
        print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
    print('To enable verification of server certificates, '
          'the CA certificate bundle must be downloaded from the server')
    sys.stdout.flush()

def prompt_server_configuration():
    if not click.confirm('Do you wish to proceed with the CA certificate bundle download?',
                         default=True):
        raise SdkCertError('Certificate bundle download was rejected')

    server_config = ServerConfig()
    print('Please answer the following questions detailing how to connect to the server')
    sys.stdout.flush()
    has_socks_proxy = click.confirm('Do you use a SOCKS proxy to connect to the server?')
    if has_socks_proxy:
        protocol_version = click.prompt('Enter SOCKS protocol version', default='5',
                                        type=click.Choice(['4', '5']))
        proxy_server = click.prompt("Enter SOCKS proxy server", default='localhost', type=str)
        proxy_port = click.prompt("Enter SOCKS proxy port", default=1080,
                                  type=click.IntRange(min=1, max=65535))
        server_config.set_socks_proxy_protocol_version(int(protocol_version))
        server_config.set_socks_proxy_host(proxy_server)
        server_config.set_socks_proxy_port(proxy_port)
    server_user_id = click.prompt("Enter user ID for connecting to the server", default='root', type=str)
    server_config.set_server_user_id(server_user_id)
    return server_config

def download_data_from_server(host, server_config):
    ssh_client = None
    try:
        ssh_client = sdk_sshclient.SdkSshClient(host, server_config)
        ssh_client.connect()

        server_hostname = ssh_client.retrieve_server_hostname()
        server_config.set_server_hostname(server_hostname)

        # We know we have a good ssh connection so now we can create the bundle target directory.
        sdk_util.create_dir_if_not_exists(sdk_util.build_config_path(host))
        cert_bundle_path = build_cert_bundle_file_path(host)

        print('Initialising transfer of CA certificate bundle from server, please wait...')
        sys.stdout.flush()
        ssh_client.transfer_ca_cert_bundle(cert_bundle_path)
        print('Transfer complete')
        print('CA certificate bundle for {0} saved to {1}'.format(host, cert_bundle_path))
        sys.stdout.flush()
    finally:
        if ssh_client:
            ssh_client.close()
