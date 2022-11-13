# Licensed Materials - Property of IBM
# 5725I71-CC011829
# (C) Copyright IBM Corp. 2015, 2020. All Rights Reserved.
# US Government Users Restricted Rights - Use, duplication or
# disclosure restricted by GSA ADP Schedule Contract with IBM Corp.

import json
import os
import zipfile
from sdk_baseimage import SdkBaseImage

EXCLUDED_ROOT_DIRECTORIES = ['store', '.cache', '.git', '.gradle',
                             '.pytest_cache', '.settings', 'qradar_appfw_venv']
EXCLUDED_DIRECTORIES = ['__pycache__', '.idea']
EXCLUDED_ROOT_FILE_PREFIXES = ('.git', '.py', '.sdkapp')
EXCLUDED_ROOT_FILES = ['qenv.ini', '.project', '.qradar_app_uuid']
EXCLUDED_FILES = ['.DS_Store']
EXCLUDED_FILE_EXTENSIONS = ('.pyc')

WARNING_MANIFEST_IMAGE = 'WARNING: image "{0}" in manifest differs from SDK image "{1}"'

def create_zip(workspace, zip_path):
    zip_file_name = os.path.basename(zip_path)
    zip_full_dir_path = os.path.dirname(os.path.realpath(zip_path))
    if not os.path.exists(zip_full_dir_path):
        os.makedirs(zip_full_dir_path)
    original_working_directory = os.getcwd()
    os.chdir(workspace.path)
    EXCLUDED_FILES.append(zip_file_name)
    workspace_paths = _retrieve_workspace_paths()
    sdk_zip_warnings = ''
    with zipfile.ZipFile(os.path.join(zip_full_dir_path, zip_file_name), 'w') as target_zip:
        for path in workspace_paths:
            sdk_zip_warnings = _add_path_to_zip(path, target_zip, workspace, sdk_zip_warnings)
    os.chdir(original_working_directory)
    print('Created package {0}'.format(zip_path))
    if sdk_zip_warnings:
        print(sdk_zip_warnings)

def _retrieve_workspace_paths():
    paths = _workspace_root_files()
    for root_directory in _workspace_root_directories():
        paths.append(root_directory)
        for dir_path, dir_names, file_names in os.walk(root_directory):
            for dir_name in dir_names:
                if dir_name not in EXCLUDED_DIRECTORIES:
                    paths.append(os.path.join(dir_path, dir_name))
            for file_name in file_names:
                if not _is_excluded_file(dir_path, file_name):
                    paths.append(os.path.join(dir_path, file_name))
    return paths

def _add_path_to_zip(path, target_zip, workspace, sdk_zip_warnings):
    if path == 'manifest.json':
        return _add_manifest_to_zip(target_zip, workspace, sdk_zip_warnings)
    if os.path.isfile(path):
        compression = zipfile.ZIP_DEFLATED
        print('Adding file: {0}'.format(path))
    else:
        compression = zipfile.ZIP_STORED
        print('Adding directory: {0}'.format(path))
    target_zip.write(path, compress_type=compression)
    return sdk_zip_warnings

def _add_manifest_to_zip(target_zip, workspace, sdk_zip_warnings):
    manifest_json = workspace.manifest.json
    if 'dev_opts' in manifest_json:
        manifest_json.pop('dev_opts')
    image_name = SdkBaseImage().manifest_image_name
    if 'image' in manifest_json:
        if manifest_json['image'] != image_name:
            sdk_zip_warnings += WARNING_MANIFEST_IMAGE.format(manifest_json['image'],
                                                              image_name)
    else:
        print('No base image specified in manifest, adding {0}'.format(image_name))
        manifest_json.update({'image': image_name})
    print('Adding file: manifest.json')
    target_zip.writestr('manifest.json', json.dumps(manifest_json),
                        compress_type=zipfile.ZIP_DEFLATED)
    return sdk_zip_warnings

def _workspace_root_files():
    return [entry for entry in os.listdir()
            if _is_valid_workspace_root_file(entry)]

def _is_valid_workspace_root_file(entry):
    return (os.path.isfile(entry) and
            entry not in EXCLUDED_ROOT_FILES and
            not entry.startswith(EXCLUDED_ROOT_FILE_PREFIXES) and
            not _is_excluded_file('.', entry))

def _workspace_root_directories():
    return [entry for entry in os.listdir()
            if _is_valid_workspace_root_directory(entry)]

def _is_valid_workspace_root_directory(entry):
    return (os.path.isdir(entry) and
            entry not in EXCLUDED_ROOT_DIRECTORIES and
            entry not in EXCLUDED_DIRECTORIES)

def _is_excluded_file(dir_path, file_name):
    return (file_name in EXCLUDED_FILES or
            file_name.endswith(EXCLUDED_FILE_EXTENSIONS) or
            _path_contains_excluded_directory(dir_path))

def _path_contains_excluded_directory(dir_path):
    return [directory for directory in EXCLUDED_DIRECTORIES if directory in dir_path]
