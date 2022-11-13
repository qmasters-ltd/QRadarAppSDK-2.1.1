# Licensed Materials - Property of IBM
# 5725I71-CC011829
# (C) Copyright IBM Corp. 2015, 2020. All Rights Reserved.
# US Government Users Restricted Rights - Use, duplication or
# disclosure restricted by GSA ADP Schedule Contract with IBM Corp.

import os
import json
import socks
import sdk_util
from sdk_exceptions import SdkServerConfigError

class ServerConfig(dict):
    ''' Holds host and proxy details for making HTTP and SSH requests to a QRadar server '''
    def __init__(self,
                 socks_proxy_protocol_version=None,
                 socks_proxy_host=None,
                 socks_proxy_port=None,
                 server_hostname=None,
                 server_user_id=None):
        dict.__init__(self,
                      socks_proxy_protocol_version=socks_proxy_protocol_version,
                      socks_proxy_host=socks_proxy_host,
                      socks_proxy_port=socks_proxy_port,
                      server_hostname=server_hostname,
                      server_user_id=server_user_id)

    @classmethod
    def build_config_json_path(cls, host):
        return sdk_util.build_config_path(host, 'config.json')

    @classmethod
    def from_host_json_file(cls, host):
        json_file_path = cls.build_config_json_path(host)
        return cls.from_json_file(json_file_path)

    @classmethod
    def from_json_file(cls, json_file_path):
        if not os.path.isfile(json_file_path):
            return cls()
        with open(json_file_path) as config_json:
            try:
                return cls(**json.load(config_json))
            except (ValueError, TypeError) as err:
                raise SdkServerConfigError('Unable to load server configuration {0}: {1}'
                                           .format(json_file_path, err))

    def save(self, host):
        config_json_path = self.build_config_json_path(host)
        try:
            with open(config_json_path, 'w') as config_json_file:
                config_json_file.write(self.to_json())
        except (TypeError, ValueError, OSError) as ce:
            raise SdkServerConfigError('Unable to save server configuration {0}: {1}'
                                       .format(config_json_path, ce))

    def to_json(self):
        for key, value in list(self.items()):
            if value is None:
                del self[key]
        return json.dumps(self, indent=4)

    def get_socks_proxy_protocol_version(self):
        return self['socks_proxy_protocol_version']

    def set_socks_proxy_protocol_version(self, proxy_protocol_version):
        self['socks_proxy_protocol_version'] = proxy_protocol_version

    def get_socks_protocol(self):
        return socks.PROXY_TYPE_SOCKS5 if self['socks_proxy_protocol_version'] == 5 \
            else socks.PROXY_TYPE_SOCKS4

    def get_socks_proxy_host(self):
        return self['socks_proxy_host']

    def set_socks_proxy_host(self, proxy_host):
        self['socks_proxy_host'] = proxy_host

    def get_socks_proxy_port(self):
        return self['socks_proxy_port']

    def set_socks_proxy_port(self, proxy_port):
        self['socks_proxy_port'] = proxy_port

    def get_server_hostname(self):
        return self['server_hostname']

    def set_server_hostname(self, hostname):
        self['server_hostname'] = hostname

    def get_server_user_id(self):
        return self['server_user_id']

    def set_server_user_id(self, user_id):
        self['server_user_id'] = user_id

    def has_socks_proxy(self):
        for key, value in list(self.items()):
            if key == 'socks_proxy_host' and value is not None:
                return True
        return False

    def get_socks_config(self):
        socks_uri = 'socks{}://{}:{}'.format(self['socks_proxy_protocol_version'],
                                             self['socks_proxy_host'],
                                             self['socks_proxy_port'])
        return {'http': socks_uri, 'https': socks_uri}
