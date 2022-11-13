# Licensed Materials - Property of IBM
# 5725I71-CC011829
# (C) Copyright IBM Corp. 2015, 2020. All Rights Reserved.
# US Government Users Restricted Rights - Use, duplication or
# disclosure restricted by GSA ADP Schedule Contract with IBM Corp.

import json
import os
import sys
import time
from packaging.version import Version, InvalidVersion
from sdk_httpclient import SdkHttpClient
from sdk_manifest import SdkManifest
import sdk_util
from sdk_exceptions import SdkApiResponseError, SdkQradarVersionError

ENDPOINT_QRADAR_VERSION = '/api/system/about?fields=external_version'
QRADAR_MIN_VERSION_DEV_APPS = Version('7.5.0')

QRADAR_API_ROOT = '/api/gui_app_framework'
ENDPOINT_APPLICATIONS = QRADAR_API_ROOT + '/applications'
ENDPOINT_APPLICATION = ENDPOINT_APPLICATIONS + '/{0}'
ENDPOINT_APPLICATION_INSTALL = '/api/gui_app_framework/application_creation_task'
ENDPOINT_APPLICATION_INSTALL_STATUS = ENDPOINT_APPLICATION_INSTALL + '/{0}'
ENDPOINT_APPLICATION_INSTALL_AUTH = ENDPOINT_APPLICATION_INSTALL_STATUS + '/auth'
ENDPOINT_APPLICATION_CANCEL = ENDPOINT_APPLICATION_INSTALL_STATUS + '?status=CANCELLED'
ENDPOINT_USERS_WITH_CAPABILITIES = '/api/config/access/users_with_capability_filter?capabilities={0}'
ENDPOINT_APPLICATION_GET_DEFN_ID = ENDPOINT_APPLICATION + '?fields=application_definition_id'
ENDPOINT_DEFINITIONS = QRADAR_API_ROOT + '/application_definitions'
ENDPOINT_DEFINITION = ENDPOINT_DEFINITIONS + '/{0}'
DEVELOPER_APPS = '/developer/applications'
ENDPOINT_DEVELOPER_APPLICATIONS = QRADAR_API_ROOT + DEVELOPER_APPS
ENDPOINT_DEVELOPER_APPLICATION = ENDPOINT_DEVELOPER_APPLICATIONS + '/{0}'

HEADERS_JSON = {'Accept': 'application/json', 'Content-Type': 'application/json'}
HEADERS_ZIP = {'Content-Type': 'application/zip'}

STATUS_CREATING = 'CREATING'
STATUS_UPGRADING = 'UPGRADING'
STATUS_AUTH_REQUIRED = 'AUTH_REQUIRED'
STATUS_RUNNING = 'RUNNING'
STATUS_ERROR = 'ERROR'

QRADAR_REST_FRAMEWORK_MISSING_ENDPOINT_CODE = 4

MSG_DEV_APPS_UNSUPPORTED_QRADAR_VERSION = ('QRadar server {0} is at version {1}\nDevelopment apps '
                                           'are supported only in version 7.5.0 or later')
MSG_PREREGISTER_SUCCESS = 'App in workspace [{0}] successfully preregistered on server {1}'
MSG_REGISTER_SUCCESS = ('App in workspace [{0}] successfully registered on server {1} '
                        'to serve requests from {2} on these ports: {3}')
MSG_UPDATE_REGISTER_SUCCESS = ('Registration of app in workspace [{0}] successfully updated on server {1} '
                               'to serve requests from {2} on these ports: {3}')
MSG_DEREGISTER_SUCCESS = 'App in workspace [{0}] successfully deregistered on server {1}'

class SdkRestClient():
    def __init__(self, qradar_console, username):
        self.http_client = SdkHttpClient.create_certified_client(qradar_console, username)

    def retrieve_qradar_version(self):
        response = self.http_client.get(ENDPOINT_QRADAR_VERSION, HEADERS_JSON)
        try:
            return Version(response.json()['external_version'])
        except (KeyError, InvalidVersion) as ve:
            raise SdkApiResponseError('Unable to determine QRadar version from server {0}: {1}'
                                      .format(self.http_client.qradar_console, ve))

    def check_development_apps_supported(self):
        qradar_version = self.retrieve_qradar_version()
        if qradar_version < QRADAR_MIN_VERSION_DEV_APPS:
            raise SdkQradarVersionError(MSG_DEV_APPS_UNSUPPORTED_QRADAR_VERSION
                                        .format(self.http_client.qradar_console, str(qradar_version)))

    def retrieve_development_apps(self):
        ''' This function performs two checks and raises an error if either fails:
            1. Does the QRadar server version support development apps?
            2. Is the developer tools API available? '''
        self.check_development_apps_supported()
        try:
            response = self.http_client.get(ENDPOINT_DEVELOPER_APPLICATIONS, HEADERS_JSON)
        except SdkApiResponseError as ae:
            if ae.api_code == QRADAR_REST_FRAMEWORK_MISSING_ENDPOINT_CODE:
                raise SdkApiResponseError('Unable to reach developer tools REST API endpoint. Possible reason:\n'
                                          'SDK developer tools JAR file is not installed on the QRadar server.\n'
                                          'For more details, see SDK documentation.')
            raise
        return response.json()

    def preregister_development_app(self, registration_details, workspace):
        response = self.http_client.post(ENDPOINT_DEVELOPER_APPLICATIONS, HEADERS_JSON,
                                         request_json=registration_details)
        print(MSG_PREREGISTER_SUCCESS.format(workspace.name,
                                             self.http_client.qradar_console))
        return response.json()

    def register_development_app(self, definition_id, registration_details, workspace):
        response = self.http_client.post(ENDPOINT_DEVELOPER_APPLICATION.format(definition_id),
                                         HEADERS_JSON, request_json=registration_details)
        host_ports = SdkManifest.extract_ports_from_registration_request(registration_details)
        print(MSG_REGISTER_SUCCESS.format(workspace.name,
                                          self.http_client.qradar_console,
                                          registration_details['ip'],
                                          host_ports))
        return response.json()

    def update_development_app(self, definition_id, registration_details, workspace):
        response = self.http_client.put(ENDPOINT_DEVELOPER_APPLICATION.format(definition_id),
                                        HEADERS_JSON, request_json=registration_details)
        host_ports = SdkManifest.extract_ports_from_registration_request(registration_details)
        print(MSG_UPDATE_REGISTER_SUCCESS.format(workspace.name,
                                                 self.http_client.qradar_console,
                                                 registration_details['ip'],
                                                 host_ports))
        return response.json()

    def deregister_development_app(self, definition_id, workspace):
        self.http_client.delete(ENDPOINT_DEVELOPER_APPLICATION.format(definition_id))
        print(MSG_DEREGISTER_SUCCESS.format(workspace.name,
                                            self.http_client.qradar_console))

    def display_app_status(self, app_id):
        response = self.http_client.get(ENDPOINT_APPLICATION.format(app_id), HEADERS_JSON)
        app_json = response.json()
        app_status = app_json['application_state']['status']

        # See if we can get some extra status info
        if app_status in (STATUS_CREATING, STATUS_UPGRADING):
            response = self.http_client.get(ENDPOINT_APPLICATION_INSTALL_STATUS.format(app_id),
                                            HEADERS_JSON)
            task_status = response.json()['status']
            if task_status not in (STATUS_CREATING, STATUS_UPGRADING):
                app_status = app_status + ':' + task_status

        print(app_id + ':' + app_status)
        self._display_app_json_errors(app_json)

    @staticmethod
    def _display_app_json_errors(app_json):
        has_errors = False
        try:
            for error in app_json['application_state']['error_messages_json']:
                print(error['message'])
                has_errors = True
        except KeyError:
            pass
        return has_errors

    def deploy_app(self, package_path, auth_user_name, upload_timeout):
        app_uuid = SdkManifest.extract_uuid_from_zip_manifest(package_path)
        app_id = self._get_app_id_for_uuid(app_uuid)
        zip_in_memory = sdk_util.load_zip_into_memory(package_path)
        self.http_client.set_upload_timeout(upload_timeout)
        if app_id is None:
            self._new_install(package_path, auth_user_name, zip_in_memory)
        else:
            self._upgrade_install(package_path, app_id, auth_user_name, zip_in_memory)

    def _get_app_id_for_uuid(self, app_uuid):
        response = self.http_client.get(ENDPOINT_APPLICATIONS, HEADERS_JSON)
        response_json = response.json()
        for app in response_json:
            if 'uuid' in app["manifest"]:
                if app["manifest"]["uuid"] == app_uuid:
                    if app["application_state"]["status"] == "ERROR":
                        return None
                    return app["application_state"]["application_id"]
        return None

    def authorize_app(self, app_id, auth_user_name):
        self._handle_auth_request(str(app_id), auth_user_name)

    def cancel_install(self, app_id):
        self.http_client.post(ENDPOINT_APPLICATION_CANCEL.format(app_id), HEADERS_JSON)
        print("Cancel request accepted for application {0}".format(str(app_id)))

    def delete_app(self, app_id):
        response = self.http_client.get(ENDPOINT_APPLICATION_GET_DEFN_ID.format(app_id),
                                        HEADERS_JSON)
        app_definition_id = response.json()['application_definition_id']
        print('Deleting application {0}'.format(str(app_id)))
        self.http_client.delete(ENDPOINT_DEFINITION.format(app_definition_id))
        print('Application {0} has been deleted'.format(str(app_id)))

    def _new_install(self, package_path, auth_user_name, zip_in_memory):
        print("Application fresh install detected")
        print("Uploading {} {} bytes".format(package_path, os.path.getsize(package_path)))
        response = self.http_client.post(ENDPOINT_APPLICATION_INSTALL, HEADERS_ZIP,
                                         request_package=zip_in_memory.read())
        task_json = response.json()
        app_id = task_json['application_id']
        print("Installing application {}".format(app_id))
        self._finish_install(task_json, app_id, auth_user_name, expected_status=STATUS_CREATING)

    def _upgrade_install(self, package_path, app_id, auth_user_name, zip_in_memory):
        print("Application upgrade detected")
        print("Uploading {} {} bytes".format(package_path, os.path.getsize(package_path)))
        response = self.http_client.put(ENDPOINT_APPLICATION.format(app_id), HEADERS_ZIP,
                                        request_package=zip_in_memory.read())
        task_json = response.json()
        self._finish_install(task_json, app_id, auth_user_name, expected_status=STATUS_UPGRADING)

    def _finish_install(self, task_json, app_id, auth_user_name, expected_status):
        task_status = task_json['status']
        print("Application {}: {}".format(app_id, task_status))
        if task_status == expected_status:
            self._wait_for_deploy_end(app_id)
        elif task_status == STATUS_AUTH_REQUIRED:
            self._handle_auth_request(str(app_id), auth_user_name)

    def _handle_auth_request(self, app_id, auth_user_name):
        capable_users = self._retrieve_capable_users(app_id)
        try:
            auth_user_id = self._retrieve_auth_user_id(auth_user_name, capable_users)
        except ValueError:
            print('Deployment of application {0} is waiting for authorization'.format(app_id))
            return

        auth_body = {}
        auth_body['user_id'] = auth_user_id
        self.http_client.post(ENDPOINT_APPLICATION_INSTALL_AUTH.format(app_id), HEADERS_JSON,
                              request_json=auth_body)
        self._wait_for_deploy_end(app_id)

    def _retrieve_capable_users(self, app_id):
        # What capabilities is the app requesting?
        auth_response = self.http_client.get(ENDPOINT_APPLICATION_INSTALL_AUTH.format(app_id),
                                             HEADERS_JSON)
        requested_capabilities = json.dumps(auth_response.json()['capabilities'])
        print('Application {} is requesting capabilities {}'.format(app_id, requested_capabilities))

        # Which QRadar users have those capabilities?
        users_response = self.http_client.get(
            ENDPOINT_USERS_WITH_CAPABILITIES.format(requested_capabilities),
            {'Allow-Hidden': 'true'})
        return users_response.json()

    def _retrieve_auth_user_id(self, auth_user_name, capable_users):
        auth_user_id = self._get_auth_user_id_from_name(auth_user_name, capable_users)
        if auth_user_id != 0:
            return auth_user_id

        # The caller must choose an authorization user from the list.
        print('These users have the requested capabilities:')
        for capable_user in capable_users:
            print('  {0}'.format(capable_user['username']))

        if len(capable_users) == 1:
            # Only one authorization user is available to select, so a simple yes or no response will do.
            # "No" means don't proceed with the deployment.
            answer = sdk_util.read_yes_no_input('Use {0} as the authorization user? (y/n): '
                                                .format(capable_users[0]['username']))
            if answer == 'y':
                return capable_users[0]['id']
            raise ValueError

        while True:
            # The caller must select one of the capable user names.
            # An empty response means don't proceed with the deployment, subject to a confirmatory "yes".
            selected_user_name = input('Select a user: ').strip()
            if len(selected_user_name) == 0:
                if sdk_util.read_yes_no_input('Stop deployment? (y/n): ') == 'y':
                    raise ValueError
            else:
                for capable_user in capable_users:
                    if capable_user['username'] == selected_user_name:
                        return capable_user['id']
                print('User name {0} not recognized'.format(selected_user_name))

    @staticmethod
    def _get_auth_user_id_from_name(auth_user_name, capable_users):
        if auth_user_name is None:
            return 0

        # The caller supplied an authorization user. Is is valid?
        for capable_user in capable_users:
            if capable_user['username'] == auth_user_name:
                print('Using supplied authorization user {0}'.format(auth_user_name))
                return capable_user['id']

        print('Supplied authorization user {0} does not have the requested capabilities'.format(auth_user_name))
        return 0

    def _wait_for_deploy_end(self, app_id):
        # Loop over the application_creation_endpoint until the deploy finishes.
        # Note that any error message is not committed to the installed_application table
        # until the very end of the deployment, so there is no point in trying to print
        # error details inside this loop.
        task_status = STATUS_CREATING
        while task_status in (STATUS_CREATING, STATUS_UPGRADING):
            task_response = self.http_client.get(ENDPOINT_APPLICATION_INSTALL_STATUS.format(app_id),
                                                 HEADERS_JSON)
            task_json = task_response.json()
            task_status = task_json['status']
            print("Application {}: {}".format(app_id, task_status))
            if task_status in (STATUS_CREATING, STATUS_UPGRADING):
                time.sleep(5)

        # Now call the applications endpoint to get the final status of the deployment.
        app_response = self.http_client.get(ENDPOINT_APPLICATION.format(app_id), HEADERS_JSON)
        app_json = app_response.json()

        app_final_status = app_json['application_state']['status']
        additional_app_details = ''

        if app_final_status != STATUS_ERROR:
            additional_app_details = ' ' + app_json['manifest']['version']

        print("Final application state: {}{}".format(app_final_status, additional_app_details))
        has_errors = self._display_app_json_errors(app_json)

        if app_final_status == STATUS_ERROR or has_errors:
            sys.exit(1)
