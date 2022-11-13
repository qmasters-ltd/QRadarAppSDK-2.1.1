# Licensed Materials - Property of IBM
# 5725I71-CC011829
# (C) Copyright IBM Corp. 2015, 2020. All Rights Reserved.
# US Government Users Restricted Rights - Use, duplication or
# disclosure restricted by GSA ADP Schedule Contract with IBM Corp.

import sdk_util

BASE_IMAGE_NAME = 'qradar-app-base:{0}'
BASE_IMAGE_ARCHIVE_FORMAT = 'qradar-app-base-{0}.xz'

class SdkBaseImage():
    def __init__(self):
        self.image_repo, self.image_tag = self.read_name_components()
        self.manifest_image_name = BASE_IMAGE_NAME.format(self.image_tag)

    def load_if_missing(self, docker):
        if docker.registry_contains_image(self.image_repo, self.image_tag):
            print('Found base image {0}:{1}'.format(self.image_repo, self.image_tag))
            return

        print('Base image {0}:{1} is not in your Docker registry'.format(self.image_repo, self.image_tag))
        base_image_archive_path = sdk_util.build_sdk_path(
            'base_image', BASE_IMAGE_ARCHIVE_FORMAT.format(self.image_tag))
        print('Loading base image from {0}...'.format(base_image_archive_path))
        docker.load_image_from_archive(base_image_archive_path)
        print('Base image loaded successfully')

    @staticmethod
    def read_name_components():
        ''' Image name format is repo:tag.
            Returns repo,tag tuple.
        '''
        version_file_path = sdk_util.build_sdk_path('base_image', 'image_name.txt')
        with open(version_file_path) as version_file:
            image_name_components = version_file.read().splitlines()[0].rpartition(':')
        if not image_name_components[0] or not image_name_components[2]:
            raise ValueError('Unable to read base image details from {0}'.format(version_file_path))
        return image_name_components[0], image_name_components[2]
