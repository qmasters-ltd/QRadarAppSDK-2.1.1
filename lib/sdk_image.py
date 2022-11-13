# Licensed Materials - Property of IBM
# 5725I71-CC011829
# (C) Copyright IBM Corp. 2015, 2020. All Rights Reserved.
# US Government Users Restricted Rights - Use, duplication or
# disclosure restricted by GSA ADP Schedule Contract with IBM Corp.

import os
import re
import shutil
from sdk_baseimage import SdkBaseImage
import sdk_dependencies
import sdk_supervisor
import sdk_util
from sdk_exceptions import SdkWorkspaceError

class SdkImage():
    def __init__(self, docker, workspace):
        self.docker = docker
        self.workspace = workspace

    @staticmethod
    def generate_image_name(workspace_dir_name):
        ''' If workspace directory name converted to lowercase is a valid image name, returns that.
            If not, strips all chars except a-z and 0-9 and returns that.
            If stripping results in an empty name, raises SdkWorkspaceError.
        '''
        lowercase_dir = workspace_dir_name.lower()
        try:
            SdkImage.validate_image_name(lowercase_dir)
            return lowercase_dir
        except ValueError:
            stripped_name = re.sub('[^a-z0-9]', '', lowercase_dir)
            if len(stripped_name) == 0:
                raise SdkWorkspaceError(
                    '{0} cannot be used as a workspace name. Please specify a different directory.'.format(
                        workspace_dir_name))
            return stripped_name

    @staticmethod
    def validate_image_name(image_name):
        ''' From docker tag documentation:
            Names may contain lower-case letters, digits and separators.
            A separator is defined as a period, one or two underscores, or one or more dashes.
            Names may not start or end with a separator.
        '''
        if not re.match(r'^[a-z0-9]+(?:(?:[._]|__|[-]*)?[a-z0-9]+)*$', image_name):
            raise ValueError('{0} is not a valid image name'.format(image_name))

    def build(self):
        SdkBaseImage().load_if_missing(self.docker)
        build_root_path = sdk_util.build_sdk_path('docker', 'build')
        self.prepare_image_build_directory(build_root_path)
        print('Building image [{0}]'.format(self.workspace.image_name))
        self.docker.build_image(self.workspace.image_name, build_root_path)
        print('Image [{0}] build completed successfully'.format(self.workspace.image_name))

    def prepare_image_build_directory(self, build_root_path):
        ''' The build directory is docker/build under the SDK installation.
            This function always deletes and recreates the directory, then
            populates it with:
              + Dockerfile/scripts/config files from the SDK installation's image_files directory
              + any scripts and dependencies from the app workspace.
        '''
        print('Preparing image build directory {0}'.format(build_root_path))
        shutil.rmtree(build_root_path, ignore_errors=True)
        os.mkdir(build_root_path)

        image_files_path = sdk_util.build_sdk_path('image_files')
        sdk_util.copy_tree(image_files_path, build_root_path, 0o755)

        dependencies_cmd = sdk_dependencies.generate_dependencies_command(self.workspace.path)
        init_cmd = sdk_dependencies.generate_init_command(self.workspace.path)

        sdk_dependencies.copy_dependencies_to_build_root(dependencies_cmd, self.workspace.path)
        sdk_dependencies.copy_container_scripts_to_build_root(self.workspace.path)

        dockerfile_path = os.path.join(build_root_path, 'Dockerfile')
        sdk_util.replace_string_in_file(dockerfile_path, 'DEPENDENCIES-PLACE-HOLDER', dependencies_cmd)
        sdk_util.replace_string_in_file(dockerfile_path, 'INIT-PLACE-HOLDER', init_cmd)
        print('Using {0}'.format(dockerfile_path))

        sdk_supervisor.prepare_supervisord_conf(self.workspace.manifest, build_root_path)

        return build_root_path

    def is_in_registry(self):
        found = self.docker.registry_contains_image(self.workspace.image_name)
        if not found:
            print('No image found for workspace [{0}]'.format(self.workspace.name))
        return found

    def remove(self):
        print('Removing image [{0}]'.format(self.workspace.image_name))
        self.docker.remove_image(self.workspace.image_name)
        print('Image [{0}] removal completed successfully'.format(self.workspace.image_name))
