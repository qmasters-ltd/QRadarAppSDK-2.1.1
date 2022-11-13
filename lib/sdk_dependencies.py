# Licensed Materials - Property of IBM
# 5725I71-CC011829
# (C) Copyright IBM Corp. 2015, 2020. All Rights Reserved.
# US Government Users Restricted Rights - Use, duplication or
# disclosure restricted by GSA ADP Schedule Contract with IBM Corp.

import os
import sdk_container
import sdk_util

# All directories beneath the app's container directory, excluding pip and rpm.
CONTAINER_DIRS = ['build', 'run', 'clean', 'service', 'conf']

CONCAT_CMD = ' && \\\n'
CONTINUE_LINE = ' \\\n'

PIP_CMD = 'pip install --no-index --disable-pip-version-check '
PIP_PATH = sdk_container.PATH_CONTAINER + '/pip'
PIP_PACKAGE_PATH = PIP_PATH + '/{0}'
PIP_CMD_PACKAGE_AND_CONCAT = PIP_CMD + PIP_PACKAGE_PATH + CONCAT_CMD
PIP_PACKAGE_AND_CONTINUE = PIP_PACKAGE_PATH + CONTINUE_LINE

# The base image includes rpm and microdnf but not yum.
# microdnf does not support installation of local packages
# so we use rpm to install.
# After rpm packages are installed, Dockerfile best practice says
# clean up /var/cache/yum to save space. Without the yum command
# we have to use microdnf for cleanup.
RPM_CMD = 'rpm -Uv --replacepkgs --excludedocs '
RPM_PACKAGE_AND_CONTINUE = sdk_container.PATH_CONTAINER + '/rpm/{0}' + CONTINUE_LINE
RPM_CLEANUP = 'microdnf clean all'

def _workspace_container_path(workspace_path, container_dir):
    return os.path.join(workspace_path, 'container', container_dir)

def generate_dependencies_command(workspace_path):
    ''' Returns a string containing a single Dockerfile RUN command
        for installing all package dependencies from the app
        workspace's container/pip and container/rpm directories.
        If there are no dependencies, an empty string is returned.
    '''
    rpms_cmd = process_rpms(_workspace_container_path(workspace_path, 'rpm'))
    pip_cmd = process_pips(_workspace_container_path(workspace_path, 'pip'))

    if rpms_cmd is None:
        if pip_cmd is None:
            return ''
        full_cmd = pip_cmd
    elif pip_cmd is None:
        full_cmd = rpms_cmd
    else:
        full_cmd = rpms_cmd + CONCAT_CMD + pip_cmd
    return 'RUN ' + full_cmd

def process_pips(pip_path):
    # pylint: disable=too-many-return-statements, too-many-branches
    if not os.path.isdir(pip_path):
        return None

    pip_dir_list = os.listdir(pip_path)

    if pip_dir_list == []:
        return None

    print('Checking Python dependency directory {0}'.format(pip_path))

    directory_package_list = []
    ordering_exists = False

    for file_name in pip_dir_list:
        print('Found file {0}'.format(file_name))
        if file_name == 'requirements.txt':
            print('WARNING: using a requirements file to identify Python packages is no longer supported\n' +
                  'WARNING: container/pip/requirements.txt will be ignored')
        elif file_name == 'ordering.txt':
            ordering_exists = True
        else:
            directory_package_list.append(file_name)

    if len(directory_package_list) == 0:
        print('WARNING: no Python packages were found')
        return None

    if ordering_exists:
        ordering_path = os.path.join(pip_path, 'ordering.txt')
        ordering_list = sdk_util.read_lines_from_file(ordering_path)
        if len(ordering_list) == 0:
            print('WARNING: ordering.txt is empty and will be ignored')
        else:
            filtered_ordering_list = _check_ordering_against_directory(
                ordering_list, directory_package_list, ordering_path)
            if len(filtered_ordering_list) == 0:
                print('WARNING: ordering.txt does not reference any existing package')
                return None
            return _build_multi_pip_commands(filtered_ordering_list)

    return _build_single_pip_command(sorted(directory_package_list))

def _build_multi_pip_commands(package_list):
    buf = ''
    for package in package_list:
        buf = buf + PIP_CMD_PACKAGE_AND_CONCAT.format(package)
    return buf[:-6]

def _build_single_pip_command(package_list):
    buf = PIP_CMD
    for package in package_list:
        buf = buf + PIP_PACKAGE_AND_CONTINUE.format(package)
    return buf[:-3]

def process_rpms(rpms_path):
    if not os.path.isdir(rpms_path):
        return None

    rpms_dir_list = os.listdir(rpms_path)

    if rpms_dir_list == []:
        return None

    print('Checking rpm dependency directory {0}'.format(rpms_path))

    directory_package_list = []
    ordering_exists = False

    for file_name in rpms_dir_list:
        print('Found file {0}'.format(file_name))
        if file_name == 'ordering.txt':
            ordering_exists = True
        else:
            directory_package_list.append(file_name)

    if len(directory_package_list) == 0:
        print('WARNING: no rpms were found')
        return None

    if ordering_exists:
        ordering_path = os.path.join(rpms_path, 'ordering.txt')
        ordering_list = sdk_util.read_lines_from_file(ordering_path)
        if len(ordering_list) == 0:
            print('WARNING: ordering.txt is empty and will be ignored')
        else:
            filtered_ordering_list = _check_ordering_against_directory(
                ordering_list, directory_package_list, ordering_path)
            if len(filtered_ordering_list) == 0:
                print('WARNING: ordering.txt does not reference any existing package')
                return None
            return _build_rpm_command(filtered_ordering_list)

    return _build_rpm_command(sorted(directory_package_list))

def _build_rpm_command(package_list):
    buf = RPM_CMD
    for package in package_list:
        buf = buf + RPM_PACKAGE_AND_CONTINUE.format(package)
    return buf[:-3] + CONCAT_CMD + RPM_CLEANUP

def generate_init_command(workspace_path):
    ''' Returns a string containing a single Dockerfile RUN command
        for executing custom init scripts from the app workspace's
        container/build directory.
        If there are no init scripts, an empty string is returned.
    '''
    cmd_string = process_init_build_scripts(_workspace_container_path(workspace_path, 'build'))

    if cmd_string is None:
        return ''
    return 'RUN ' + cmd_string

def process_init_build_scripts(init_build_path):
    if not os.path.isdir(init_build_path):
        return None

    init_build_dir_list = os.listdir(init_build_path)

    if init_build_dir_list == []:
        return None

    print('Checking custom scripts directory {0}'.format(init_build_path))

    ordering_exists = False

    for file_name in init_build_dir_list:
        print('Found file {0}'.format(file_name))
        if file_name == 'ordering.txt':
            ordering_exists = True

    if not ordering_exists:
        print('WARNING: ignoring custom scripts directory {0} because ordering.txt is missing'.format(init_build_path))
        return None

    ordering_path = os.path.join(init_build_path, 'ordering.txt')
    ordering_list = sdk_util.read_lines_from_file(ordering_path)
    if len(ordering_list) == 0:
        print('WARNING: ignoring custom scripts directory {0} because ordering.txt is empty'.format(init_build_path))
        return None

    return _build_init_command(ordering_list)

def _build_init_command(ordering_list):
    buf = ''
    for cmd in ordering_list:
        buf = buf + cmd + CONCAT_CMD
    return buf[:-6]

def _check_ordering_against_directory(ordering_list, directory_package_list, ordering_path):
    filtered_ordering_list = []

    for ordering_package in ordering_list:
        if ordering_package in directory_package_list:
            filtered_ordering_list.append(ordering_package)
        else:
            print('WARNING: {0} references non-existent package {1}'.format(ordering_path, ordering_package))

    for dir_package in directory_package_list:
        if dir_package not in ordering_list:
            print('WARNING: {0} does not reference package {1}'.format(ordering_path, dir_package))

    return filtered_ordering_list

def copy_dependencies_to_build_root(dependencies_cmd, workspace_path):
    ''' Creates directories container/pip and container/rpm under the build root directory.
        Copies to those locations any pip and rpm package files from the workspace.
    '''
    build_pip_path = sdk_util.build_sdk_path('docker', 'build', 'container', 'pip')
    os.makedirs(build_pip_path)
    if PIP_CMD in dependencies_cmd:
        print('Copying Python packages to {0}'.format(build_pip_path))
        sdk_util.copy_tree(_workspace_container_path(workspace_path, 'pip'), build_pip_path)

    build_rpms_path = sdk_util.build_sdk_path('docker', 'build', 'container', 'rpm')
    os.makedirs(build_rpms_path)
    if RPM_CMD in dependencies_cmd:
        print('Copying rpm packages to {0}'.format(build_rpms_path))
        sdk_util.copy_tree(_workspace_container_path(workspace_path, 'rpm'), build_rpms_path)

def copy_container_scripts_to_build_root(workspace_path):
    for container_dir in CONTAINER_DIRS:
        _copy_container_dir_to_build_root(workspace_path, container_dir)

def _copy_container_dir_to_build_root(workspace_path, container_dir):
    ''' Creates directory named container/<container_dir> under the build root directory.
        Copies to that location any container/<container_dir> files from the workspace,
        and sets executable permission on those files.
    '''
    build_container_path = sdk_util.build_sdk_path('docker', 'build', 'container', container_dir)
    os.makedirs(build_container_path)
    workspace_container_path = _workspace_container_path(workspace_path, container_dir)
    if os.path.isdir(workspace_container_path):
        print('Copying scripts to {0}'.format(build_container_path))
        sdk_util.copy_tree(workspace_container_path, build_container_path, 0o755)
