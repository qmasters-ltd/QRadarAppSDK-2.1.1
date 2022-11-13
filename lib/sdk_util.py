# Licensed Materials - Property of IBM
# 5725I71-CC011829
# (C) Copyright IBM Corp. 2015, 2020. All Rights Reserved.
# US Government Users Restricted Rights - Use, duplication or
# disclosure restricted by GSA ADP Schedule Contract with IBM Corp.

import getpass
import io
import os
import re
import shutil
import subprocess
from sys import platform

def read_password(user):
    test_password = os.getenv('SDK_TEST_PWD')
    if test_password:
        return test_password
    return getpass.getpass('Please enter password for user ' + user + ':')

def read_yes_no_input(message):
    answer = ''
    while True:
        answer = input(message).strip().lower()
        if answer in ('y', 'yes'):
            return 'y'
        if answer in ('n', 'no'):
            return 'n'

def build_sdk_path(*path_entries):
    ''' Builds path to an entry under the SDK installation.
        The path is generated using the grandparent directory of this file.
    '''
    sdk_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    return os.path.join(sdk_path, *path_entries)

def build_manifest_schema_path():
    return build_sdk_path('conf', 'manifest-schema.json')

def build_config_path(*path_entries):
    ''' Builds path to an entry under the SDK's .qradar_app_sdk config directory.
        The path is generated starting from SDK_INSTALL_HOME, or the
        user's home directory if SDK_INSTALL_HOME is not set.
    '''
    sdk_install_home = os.getenv('SDK_INSTALL_HOME', os.path.expanduser('~'))
    return os.path.join(sdk_install_home, '.qradar_app_sdk', *path_entries)

def remove_host_config(host):
    ''' Removes the .qradar_app_sdk/<host> directory, thus deleting
        any server configuration and downloaded cert bundle for that host.
    '''
    try:
        shutil.rmtree(build_config_path(host))
    except OSError:
        pass

def strip_errno_prefix(error_text):
    ''' Strips [Errno X] from a Python error message. '''
    return re.sub(r'\[Errno \d+\][ ]*', '', error_text)

def copy_tree(source, destination, mode=None):
    for _file in os.listdir(source):
        _src = os.path.join(source, _file)
        _dst = os.path.join(destination, _file)

        if os.path.isdir(_src):
            if not os.path.exists(_dst):
                os.mkdir(_dst)
            copy_tree(_src, _dst, mode)
        else:
            shutil.copy(_src, _dst)
            if mode is not None:
                os.chmod(_dst, mode)

def read_lines_from_file(file_path):
    ''' Strips leading/trailing whitespace from each line
        and removes blank lines.
    '''
    lines_list = []
    with open(file_path) as _:
        for line in _:
            stripped_line = line.strip()
            if stripped_line:
                lines_list.append(stripped_line)
    return lines_list

def replace_string_in_file(file_path, target_string, replacement):
    with open(file_path) as _:
        content = _.read()
    modified_content = re.sub(target_string, replacement, content)
    with open(file_path, 'w') as _:
        _.write(modified_content)

def load_zip_into_memory(zip_path):
    with open(zip_path, 'rb') as app_zip:
        in_memory_file = io.BytesIO()
        in_memory_file.write(app_zip.read())
        in_memory_file.seek(0)
        return in_memory_file

def is_os_linux():
    return platform.startswith('linux')

def host_docker_internal_exists():
    with open('/etc/hosts') as hosts_file:
        hosts = hosts_file.readlines()
    for line in hosts:
        if "host.docker.internal" in line:
            return True
    return False

def retrieve_linux_docker_host_ip():
    process = subprocess.run(['ip', 'addr', 'show', 'docker0'],
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             universal_newlines=True,
                             check=False)

    if process.returncode != 0:
        error_text = re.sub('\n', '', process.stderr)
        raise OSError(error_text)

    try:
        host_ip = process.stdout.split("inet ")[1].split("/")[0]
    except IndexError:
        host_ip = ''

    if len(host_ip.strip()) == 0:
        raise OSError('Failed to extract IP address from output of command "ip addr show docker0"')

    return host_ip

def env_var_is_true(env_var):
    return os.getenv(env_var, 'false').lower() == 'true'

def create_dir_if_not_exists(dir_to_create):
    os.makedirs(dir_to_create, exist_ok=True)
