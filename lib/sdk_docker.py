# Licensed Materials - Property of IBM
# 5725I71-CC011829
# (C) Copyright IBM Corp. 2015, 2020. All Rights Reserved.
# US Government Users Restricted Rights - Use, duplication or
# disclosure restricted by GSA ADP Schedule Contract with IBM Corp.

import docker
import os
import re
import requests
import time
from sdk_exceptions import SdkDockerError, SdkContainerError
import sdk_util

DOCKER_CONNECT_ERROR = 'Unable to connect to Docker. Please check that Docker is running.'

class SdkDockerClient():
    CONTAINER_PORT = '5000/tcp'

    def __init__(self):
        try:
            self.docker_client = docker.from_env(version='auto')
        except docker.errors.DockerException:
            raise SdkDockerError(DOCKER_CONNECT_ERROR)

    @staticmethod
    def _handle_connection_error():
        raise SdkDockerError(DOCKER_CONNECT_ERROR)

    @staticmethod
    def _handle_docker_error(error):
        raise SdkDockerError('Docker error: {0}'.format(error))

    def _handle_docker_image_build_error(self, error):
        self._print_build_log(error.build_log)
        print('Cleaning up build remnants')
        self.prune_containers()
        self.prune_images()
        raise SdkDockerError('Build failed: see DOCKER BUILD LOG above for error details')

    @staticmethod
    def _print_build_log(build_log):
        print('DOCKER BUILD LOG: START')
        # Each line in build_log is represented by an object.
        # Lines without 'stream' or 'errorDetail' fields are ignored.
        for line in build_log:
            if 'stream' in line:
                # Ignore lines that aren't useful.
                if SdkDockerClient._suppress_stream_line(line['stream']):
                    continue
                # Remove newlines so that output is compact.
                line_text = re.sub('\n', '', line['stream'])
                # Ignore lines that are empty.
                if len(line_text) == 0:
                    continue
            elif 'errorDetail' in line:
                line_text = line['error']
            else:
                continue
            # To improve readability of long command lines, insert a newline
            # after each '&&'.
            print(re.sub(' && ', ' && \\\n', line_text), flush=True)
        print('DOCKER BUILD LOG: END')

    @staticmethod
    def _suppress_stream_line(line):
        return '--->' in line or \
            'Removing intermediate container' in line or \
            "WARNING: Running pip as the 'root' user" in line

    def check_docker_is_running(self):
        try:
            self.docker_client.ping()
        except requests.ConnectionError:
            self._handle_connection_error()
        except (docker.errors.DockerException) as de:
            self._handle_docker_error(de)

    def retrieve_image(self, image_name):
        try:
            return self.docker_client.images.get(image_name)
        except docker.errors.ImageNotFound:
            return None
        except requests.ConnectionError:
            self._handle_connection_error()
        except (docker.errors.DockerException) as de:
            self._handle_docker_error(de)

    def registry_contains_image(self, image_repo, image_tag='latest'):
        return self.retrieve_image(image_repo + ':' + image_tag) is not None

    def load_image_from_archive(self, image_archive_path):
        with open(image_archive_path, 'rb') as image_data:
            try:
                self.docker_client.images.load(image_data)
            except requests.ConnectionError:
                self._handle_connection_error()
            except (docker.errors.DockerException) as de:
                self._handle_docker_error(de)

    def build_image(self, image_name, build_path):
        user_id = str(os.getuid())
        group_id = str(os.getgid())
        args = {'APP_USER_ID': user_id, 'APP_GROUP_ID': group_id}
        print('Using user ID {0} and group ID {1}'.format(user_id, group_id))
        try:
            _, build_log = self.docker_client.images.build(path=build_path, tag=image_name,
                                                           buildargs=args, rm=True)
            self._print_build_log(build_log)
        except (docker.errors.BuildError) as be:
            self._handle_docker_image_build_error(be)
        except requests.ConnectionError:
            self._handle_connection_error()
        except (docker.errors.DockerException) as de:
            self._handle_docker_error(de)

    def prune_containers(self):
        try:
            self.docker_client.containers.prune(filters={'label': 'com.ibm.si.app.origin=SDK'})
        except (requests.ConnectionError, docker.errors.DockerException) as de:
            print('An error occurred while cleaning up containers: {0}'.format(de))

    def prune_images(self):
        try:
            self.docker_client.images.prune(filters={'dangling': True})
        except (requests.ConnectionError, docker.errors.DockerException) as de:
            print('An error occurred while removing dangling images: {0}'.format(de))

    def remove_image(self, image_name):
        try:
            self.docker_client.images.remove(image=image_name, force=True)
        except requests.ConnectionError:
            self._handle_connection_error()
        except (docker.errors.DockerException) as de:
            self._handle_docker_error(de)

    @staticmethod
    def build_mount(source_path, target_path):
        return docker.types.Mount(target_path, source_path, type='bind')

    def retrieve_container(self, container_name):
        try:
            return self.docker_client.containers.get(container_name)
        except (docker.errors.NotFound, requests.exceptions.ChunkedEncodingError):
            raise SdkContainerError('Container {0} not found'.format(container_name))
        except requests.ConnectionError:
            self._handle_connection_error()
        except (docker.errors.DockerException) as de:
            self._handle_docker_error(de)

    def remove_container(self, container):
        ''' Use container.stop() to allow the container to shut down gracefully.
            After that the container should be removed automatically thanks to
            the auto_remove flag supplied at startup.
        '''
        try:
            container.stop()
            self._wait_for_container_remove_complete(container.name)
        except requests.ConnectionError:
            self._handle_connection_error()
        except (docker.errors.DockerException) as de:
            self._handle_docker_error(de)

    def _wait_for_container_remove_complete(self, container_name):
        while True:
            try:
                self.retrieve_container(container_name)
                time.sleep(5)
            except SdkContainerError:
                return

    def run(self, image_name, container_name, app_mounts, env_vars,
            port_mappings, memory_limit, show_logs):
        extra_hosts = self._generate_extra_hosts()
        try:
            container = self.docker_client.containers.run(image_name,
                                                          name=container_name,
                                                          mem_limit=memory_limit,
                                                          ports=port_mappings,
                                                          mounts=app_mounts,
                                                          environment=env_vars,
                                                          extra_hosts=extra_hosts,
                                                          auto_remove=True,
                                                          detach=True)
        except requests.ConnectionError:
            self._handle_connection_error()
        except (docker.errors.DockerException) as de:
            self._handle_docker_error(de)

        if show_logs:
            self._print_container_logs(container)
        container.reload()
        return container

    @staticmethod
    def _print_container_logs(container):
        logs = container.logs(stream=True, follow=True)
        print('CONTAINER LOGS: START')
        try:
            while True:
                # next(log) return type is bytes, so we need to decode to a string.
                # We use default encoding utf-8 and ignore any errors.
                print(next(logs).decode(errors='ignore').split('\n')[0])
        except StopIteration:
            pass
        except KeyboardInterrupt:
            print('')
        print('CONTAINER LOGS: END')

    @staticmethod
    def _generate_extra_hosts():
        ''' Inside the app container, if we need to use a proxy to e.g.
            make REST calls to the QRadar console, and if the proxy refers
            to the container host, then we need the container host's name
            or IP address.
            On Mac and Windows, Docker provides host.docker.internal.
            On Linux, we have to look up the host IP and then add a
            host.docker.internal entry to /etc/hosts.
        '''
        extra_hosts = {}
        # add to extra_hosts if host.docker.internal doesn't exist
        if sdk_util.host_docker_internal_exists():
            return extra_hosts
        if sdk_util.is_os_linux():
            try:
                docker_host_ip = sdk_util.retrieve_linux_docker_host_ip()
                extra_hosts['host.docker.internal'] = docker_host_ip
            except OSError as oe:
                raise SdkDockerError('Unable to determine docker host IP address: {0}'.format(oe))
        return extra_hosts
