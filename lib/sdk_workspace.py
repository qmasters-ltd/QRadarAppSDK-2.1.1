# Licensed Materials - Property of IBM
# 5725I71-CC011829
# (C) Copyright IBM Corp. 2015, 2020. All Rights Reserved.
# US Government Users Restricted Rights - Use, duplication or
# disclosure restricted by GSA ADP Schedule Contract with IBM Corp.

import os
import configparser
import json
import uuid
from sdk_image import SdkImage
from sdk_manifest import SdkManifest
import sdk_util
from sdk_exceptions import SdkWorkspaceError

class SdkWorkspace():
    def __init__(self, workspace_dir,
                 check_dir_name=True,
                 check_dir_exists=True,
                 check_content=True,
                 check_secret_uuid=False):
        self.path = os.path.realpath(workspace_dir)
        self.name = os.path.basename(self.path)
        self.image_name = None
        self.manifest = None
        self.secret_uuid = None
        try:
            self.image_name = SdkImage.generate_image_name(self.name)
        except SdkWorkspaceError:
            if check_dir_name:
                raise
        if check_dir_exists:
            self._check_workspace_directory_exists()
        if check_content:
            self._check_workspace_content()
            self.manifest = SdkManifest.from_workspace(self.path)
        if check_secret_uuid:
            try:
                self.secret_uuid = self._read_secret_uuid_file()
            except SdkWorkspaceError:
                self.secret_uuid = self._create_secret_uuid_file()

    def _check_workspace_directory_exists(self):
        if not os.path.isdir(self.path):
            raise SdkWorkspaceError('Directory {0} does not exist'.format(self.path))

    def _check_workspace_content(self):
        if not os.path.isdir(os.path.join(self.path, 'app')):
            raise SdkWorkspaceError('Workspace {0} does not contain an app directory'.format(self.name))
        try:
            with open(os.path.join(self.path, 'manifest.json')) as manifest_file:
                SdkManifest.validate_workspace_manifest(manifest_file)
        except FileNotFoundError:
            raise SdkWorkspaceError('Workspace {0} does not contain a manifest.json file'.format(self.name))

    def populate_from_template(self, app_uuid):
        template_source_dir = sdk_util.build_sdk_path("template")
        print("Template source directory: " + template_source_dir)
        print("Destination directory: " + self.path)
        if not os.path.exists(self.path):
            print('Creating directories')
            os.makedirs(self.path)
        print('Adding template files and directories')
        sdk_util.copy_tree(template_source_dir, self.path)
        log_path = os.path.join(self.path, 'store', 'log')
        if not os.path.exists(log_path):
            os.makedirs(log_path)
        print('Adding uuid to manifest.json')
        manifest_json = SdkManifest.from_workspace(self.path).json
        manifest_json.update({'uuid': app_uuid})
        with open(os.path.join(self.path, 'manifest.json'), 'w') as manifest_file:
            json.dump(manifest_json, manifest_file, indent=2)
        print('Workspace [{0}] is ready'.format(self.name))

    def app_details_file_path(self, qconsole_ip):
        return os.path.join(self.path, '.sdkapp-' + qconsole_ip)

    def app_uuid_file_path(self):
        return os.path.join(self.path, '.qradar_app_uuid')

    def retrieve_dev_app_instance_id(self, qconsole_ip):
        try:
            with open(self.app_details_file_path(qconsole_ip)) as _:
                return json.load(_)['instance_id']
        except (OSError, KeyError, ValueError, TypeError):
            print('No development app for workspace [{0}] has been preregistered against {1}'
                  .format(self.name, qconsole_ip))

    def _create_secret_uuid_file(self):
        app_uuid = str(uuid.uuid4())
        try:
            with open(self.app_uuid_file_path(), 'w') as _:
                _.write(app_uuid)
                return app_uuid
        except OSError as oe:
            raise SdkWorkspaceError('Unable to create app container uuid file in workspace: {0}'.format(oe))

    def _read_secret_uuid_file(self):
        try:
            with open(self.app_uuid_file_path()) as _:
                return _.readline().strip()
        except OSError as oe:
            raise SdkWorkspaceError('Unable to read app container uuid file in workspace: {0}'.format(oe))

    def generate_env_vars(self, dev_app_instance_id=None, use_dev_env=False, cert_path=None):
        ''' Generates these environment variable settings for the app container:
            QRADAR_APPFW_SDK    Always set to true, used by qpylib.
            QRADAR_APP_UUID     Set to the secret uuid stored in the app workspace.
                                Used as a substitute for the uuid that is generated server-side
                                for a deployed app.
            QRADAR_APP_ID       Set to dev_app_instance_id, if supplied.
            FLASK_ENV           Set to "development" if use_dev_env=True.
            REQUESTS_CA_BUNDLE  Set to cert_path, if supplied.
        '''
        print('Configuring container environment')
        env_vars = {'QRADAR_APPFW_SDK': 'true', 'QRADAR_APP_UUID': self.secret_uuid}
        app_id_set = False
        if dev_app_instance_id:
            print('Setting QRADAR_APP_ID using development app ID')
            env_vars['QRADAR_APP_ID'] = dev_app_instance_id
            app_id_set = True
        if use_dev_env:
            self._add_env_var(env_vars, 'FLASK_ENV', 'development')
        if cert_path:
            self._add_env_var(env_vars, 'REQUESTS_CA_BUNDLE', cert_path)
        self._add_qenv_vars(env_vars, os.path.join(self.path, 'qenv.ini'), app_id_set)
        return env_vars

    def _add_qenv_vars(self, env_vars, qenv_ini_path, app_id_set):
        if not os.path.exists(qenv_ini_path):
            print('No qenv.ini file found in workspace')
            return
        print('Reading environment variables from {0}'.format(qenv_ini_path))
        var_set = False
        env_config = configparser.ConfigParser()
        try:
            env_config.read(qenv_ini_path)
        except configparser.Error as ce:
            raise SdkWorkspaceError('Unable to parse qenv.ini: {0}'.format(ce))
        for section in env_config.sections():
            for key in env_config[section]:
                env_key = key.upper()
                value = env_config[section][key]
                if value:
                    if env_key == 'QRADAR_APPFW_SDK':
                        if value.lower() != 'true':
                            print('Ignoring QRADAR_APPFW_SDK')
                    elif env_key == 'QRADAR_APP_ID' and app_id_set:
                        print('Ignoring QRADAR_APP_ID, already set')
                    else:
                        self._add_env_var(env_vars, env_key, value)
                        var_set = True
                else:
                    print('Ignoring empty variable {0}'.format(env_key))
        if not var_set:
            print('No environment variables from qenv.ini were set')

    @staticmethod
    def _add_env_var(env_vars, env_key, value):
        print('Setting {0}'.format(env_key))
        env_vars[env_key] = value
