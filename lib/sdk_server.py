# Licensed Materials - Property of IBM
# 5725I71-CC011829
# (C) Copyright IBM Corp. 2015, 2020. All Rights Reserved.
# US Government Users Restricted Rights - Use, duplication or
# disclosure restricted by GSA ADP Schedule Contract with IBM Corp.

import json
import sdk_util
from sdk_exceptions import SdkServerConfigError

class SdkServer():
    ''' Holds default values for SDK action -q and -u options.
        Manages writing to and reading from disk.
    '''

    MSG_SERVER_AND_USER_MISSING = 'Use the -q and -u options to identify a QRadar server and user'
    MSG_SERVER_MISSING = 'Use the -q option to identify a QRadar server'
    MSG_USER_MISSING = 'Use the -u option to identify a QRadar user'
    MSG_SAVE_SUCCESS = 'QRadar server [{0}] and QRadar user [{1}] are set as defaults for all SDK actions'

    def __init__(self, qserver_ip, quser_id):
        self.qserver_ip = qserver_ip
        self.quser_id = quser_id

    @staticmethod
    def server_details_path():
        return sdk_util.build_config_path('qserver.json')

    @classmethod
    def resolve(cls, qapp_args, print_details=False):
        ''' 1. Server details, if they exist, are read from the SDK's .qradar_app_sdk directory.
            2. If server details are supplied in qapp_args, these override the details from step 1.
            3. If either the server IP or user ID is missing from the resolved details,
               SdkServerConfigError is raised.
            4. If server details were supplied in qapp_args, the resolved details are saved back
               to the .qradar_app_sdk directory.
            5. An SdkServer object is returned.
        '''
        qserver_ip, quser_id = SdkServer.read_config()

        save_required = False

        if qapp_args.qradar_console:
            qserver_ip = qapp_args.qradar_console
            save_required = True

        if qapp_args.user:
            quser_id = qapp_args.user
            save_required = True

        if print_details:
            print('QRadar server: {0}\nQRadar user: {1}'.format(qserver_ip, quser_id))

        if not qserver_ip and not quser_id:
            raise SdkServerConfigError(cls.MSG_SERVER_AND_USER_MISSING)

        if not qserver_ip:
            raise SdkServerConfigError(cls.MSG_SERVER_MISSING)

        if not quser_id:
            raise SdkServerConfigError(cls.MSG_USER_MISSING)

        server = cls(qserver_ip, quser_id)

        if save_required:
            server.save(print_details)

        return server

    @staticmethod
    def read_config():
        ''' Returns a tuple containing the QRadar server IP and user as stored
            in .qradar_app_sdk/qserver.json. If those details do not exist or
            for any reason cannot be read in full, a tuple of empty strings is returned.
        '''
        try:
            with open(SdkServer.server_details_path()) as server_details_file:
                server_details = json.load(server_details_file)
            qserver_ip = server_details['ip']
            quser_id = server_details['user']
        except (OSError, ValueError, KeyError):
            qserver_ip = ''
            quser_id = ''
        return (qserver_ip, quser_id)

    def save(self, print_save_message):
        try:
            with open(SdkServer.server_details_path(), 'w') as server_details_file:
                json.dump({'ip': self.qserver_ip, 'user': self.quser_id}, server_details_file)
        except OSError as oe:
            raise SdkServerConfigError('Unable to save server details: {0}'.format(oe))

        if print_save_message:
            print(self.MSG_SAVE_SUCCESS.format(self.qserver_ip, self.quser_id))
