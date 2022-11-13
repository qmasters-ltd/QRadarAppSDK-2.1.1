# Licensed Materials - Property of IBM
# 5725I71-CC011829
# (C) Copyright IBM Corp. 2015, 2020. All Rights Reserved.
# US Government Users Restricted Rights - Use, duplication or
# disclosure restricted by GSA ADP Schedule Contract with IBM Corp.

import os
import json
from sdk_exceptions import SdkApiResponseError, SdkWorkspaceError

class SdkDeveloperApp():
    ''' Holds details about a development app registered on a specific QRadar console.
        Manages writing to and reading from disk.
    '''
    def __init__(self, app_definition_id, app_instance_id, app_status, qconsole_ip):
        self.definition_id = app_definition_id
        self.instance_id = app_instance_id
        self.status = app_status
        self.qconsole_ip = qconsole_ip

    def is_preregistered(self):
        return self.status == 'CREATING'

    def is_registered(self):
        return self.status == 'RUNNING'

    def state(self):
        if self.is_preregistered():
            return 'preregistered'
        return 'registered'

    @classmethod
    def from_api_response(cls, response_json, qconsole_ip):
        try:
            return cls(response_json['definition_id'],
                       response_json['instance_id'],
                       response_json['status'],
                       qconsole_ip)
        except KeyError as ke:
            raise SdkApiResponseError('Unable to extract registered app details from server response: {0}'.format(ke))

    @classmethod
    def from_workspace(cls, workspace, qconsole_ip, qconsole_dev_apps):
        ''' If there are app details stored against qconsole_ip in the workspace,
            and if those details match an entry in the qconsole_dev_apps list,
            then an SdkDeveloperApp object constructed from the list entry is returned.
            Otherwise, None is returned, indicating that server qconsole_ip has no
            dev app corresponding to the given workspace.
        '''
        try:
            with open(workspace.app_details_file_path(qconsole_ip)) as app_details_file:
                app_details = json.load(app_details_file)
            for registered_app in qconsole_dev_apps:
                if registered_app['definition_id'] == app_details['definition_id']:
                    return cls(registered_app['definition_id'],
                               registered_app['instance_id'],
                               registered_app['status'],
                               qconsole_ip)
        except (OSError, ValueError, KeyError):
            pass
        return None

    def save(self, workspace):
        try:
            with open(workspace.app_details_file_path(self.qconsole_ip), 'w') as app_details_file:
                json.dump({'definition_id': self.definition_id,
                           'instance_id': self.instance_id},
                          app_details_file)
        except OSError as oe:
            raise SdkWorkspaceError('Unable to save registered app details to workspace [{0}]: {1}'
                                    .format(os.path.basename(workspace.path), oe))

    # This is a static method so that we can call it without caring about the existence
    # of the app details file.
    @staticmethod
    def remove(workspace, qconsole_ip):
        app_details_path = workspace.app_details_file_path(qconsole_ip)
        if os.path.exists(app_details_path):
            try:
                os.remove(app_details_path)
            except OSError as oe:
                raise SdkWorkspaceError('Unable to remove registered app details from workspace [{0}]: {1}'
                                        .format(os.path.basename(workspace.path), oe))
