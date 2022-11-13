# Licensed Materials - Property of IBM
# 5725I71-CC011829
# (C) Copyright IBM Corp. 2015, 2020. All Rights Reserved.
# US Government Users Restricted Rights - Use, duplication or
# disclosure restricted by GSA ADP Schedule Contract with IBM Corp.

import json
import sdk_util
from sdk_exceptions import SdkBaseImageError

class SdkBaseImageConfig():
    BASE_IMAGE_SHORT_NAME = 'qradar-app-base'
    BASE_IMAGE_FULL_NAME = f'docker-release.secintel.intranet.ibm.com/gaf/{BASE_IMAGE_SHORT_NAME}'

    def __init__(self):
        self.v2_version, self.v3_version = self.read_sdk_versions()

    @staticmethod
    def read_sdk_versions():
        versions_file_path = sdk_util.build_sdk_path('base_image', 'versions.json')
        try:
            with open(versions_file_path) as versions_file:
                versions = json.load(versions_file)
                return versions['v2'], versions['v3']
        except (KeyError, ValueError, OSError):
            raise SdkBaseImageError(f'Unable to read base image versions from {versions_file_path}')

    def versions(self):
        return [self.v2_version, self.v3_version]

    def print_image_details(self):
        print('Base image            | Python version | Compatible QRadar versions')
        print('----------------------+----------------+---------------------------')
        print(f'{SdkBaseImageConfig.generate_short_name_with_version(self.v2_version)} | 3.6            | All')
        print(f'{SdkBaseImageConfig.generate_short_name_with_version(self.v3_version)} | 3.8            | 7.5.0 UP3+')

    def default_version(self):
        return self.v2_version

    def default_manifest_image(self):
        return f'{SdkBaseImageConfig.BASE_IMAGE_SHORT_NAME}:{self.default_version()}'

    def resolve_version_for_image_build(self, manifest_image_version):
        if not manifest_image_version:
            raise SdkBaseImageError('No image supplied in manifest.json, unable to select from available '
                                    f'SDK base image versions: {self.versions()}')
        if manifest_image_version in self.versions():
            return manifest_image_version
        raise SdkBaseImageError(f'Image version {manifest_image_version} in manifest.json '
            f'does not match any available SDK base image version: {self.versions()}')

    @staticmethod
    def generate_archive_path(base_image_version):
        return sdk_util.build_sdk_path('base_image',
                                       f'{SdkBaseImageConfig.BASE_IMAGE_SHORT_NAME}-{base_image_version}.xz')

    @staticmethod
    def generate_short_name_with_version(base_image_version):
        return f'{SdkBaseImageConfig.BASE_IMAGE_SHORT_NAME}:{base_image_version}'

    @staticmethod
    def generate_full_name_with_version(base_image_version):
        return f'{SdkBaseImageConfig.BASE_IMAGE_FULL_NAME}:{base_image_version}'
