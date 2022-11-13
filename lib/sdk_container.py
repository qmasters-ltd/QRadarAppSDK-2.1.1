# Licensed Materials - Property of IBM
# 5725I71-CC011829
# (C) Copyright IBM Corp. 2015, 2020. All Rights Reserved.
# US Government Users Restricted Rights - Use, duplication or
# disclosure restricted by GSA ADP Schedule Contract with IBM Corp.

import os
import sdk_util
from sdk_certificates import build_cert_bundle_file_path
from sdk_exceptions import SdkDockerError, SdkContainerError

APP_ROOT = '/opt/app-root'
PATH_MANIFEST = APP_ROOT + '/manifest.json'
PATH_APP = APP_ROOT + '/app'
PATH_CONTAINER = APP_ROOT + '/container'
PATH_STORE = APP_ROOT + '/store'
PATH_CERTS = '/etc/qradar_pki/ca-bundle.crt'

class SdkContainer():
    def __init__(self, docker, workspace, running=True):
        self.docker = docker
        self.name = 'qradar-{0}'.format(workspace.image_name)
        self.workspace = workspace
        self.container = None
        try:
            self.container = self.docker.retrieve_container(self.name)
        except SdkContainerError:
            if running:
                print('No container found for workspace [{0}]'.format(workspace.name))
                raise
        if self.container and not running:
            self._prompt_remove_running_container()

    def _prompt_remove_running_container(self):
        print('A container named [{0}] already exists'.format(self.name))
        answer = sdk_util.read_yes_no_input('Remove existing container? (y/n): ')
        if answer == 'n':
            raise SdkDockerError('Aborting run: container [{0}] with ID {1} is still running'
                                 .format(self.name, self.container.short_id))
        self.remove()

    def run(self, flask_host_port, show_logs, use_dev_env, qconsole, dev_app_instance_id):
        print('Starting container [{0}] using image [{1}]'.format(self.name, self.workspace.image_name))
        env_vars = self.workspace.generate_env_vars(dev_app_instance_id, use_dev_env,
                                                    PATH_CERTS if qconsole else None)
        app_mounts = self._build_app_container_mounts(qconsole)
        requested_port_mappings = self._build_requested_port_mappings(flask_host_port)
        memory_limit = self._determine_memory_limit()

        self.container = self.docker.run(self.workspace.image_name, self.name, app_mounts, env_vars,
                                         requested_port_mappings, memory_limit, show_logs)

        assigned_port_mappings = self.retrieve_assigned_port_mappings()
        flask_mode = self._determine_flask_mode(use_dev_env)
        self._print_run_status(assigned_port_mappings, flask_mode)

    def _build_mount(self, source_path, target_path):
        print('Mounting {0} to {1}'.format(source_path, target_path))
        return self.docker.build_mount(source_path, target_path)

    def _build_app_container_mounts(self, qconsole):
        manifest_mount = self._build_mount(os.path.join(self.workspace.path, 'manifest.json'), PATH_MANIFEST)
        app_mount = self._build_mount(os.path.join(self.workspace.path, 'app'), PATH_APP)
        store_path = os.path.join(self.workspace.path, 'store')
        if not os.path.exists(store_path):
            print('Creating store directory {0}'.format(store_path))
            os.mkdir(store_path)
        store_mount = self._build_mount(store_path, PATH_STORE)
        mounts = [manifest_mount, app_mount, store_mount]
        if qconsole:
            certs_mount = self._build_mount(build_cert_bundle_file_path(qconsole), PATH_CERTS)
            mounts.append(certs_mount)
        return mounts

    def _print_run_status(self, assigned_port_mappings, flask_mode):
        # Container status values: created|restarting|running|removing|paused|exited|dead
        if self.container.status in ('created', 'running'):
            print('Container [{0}] started with ID {1}'.format(self.name, self.container.short_id))
            for container_port, host_port in assigned_port_mappings.items():
                print('Host port {0} is mapped to container port {1}'.format(host_port, container_port))
            if flask_mode:
                print('Flask is running in {0} mode'.format(flask_mode))
                flask_host_port = assigned_port_mappings['5000/tcp']
                print('Access Flask endpoints at http://localhost:{0}'.format(flask_host_port))
        else:
            print('Container [{0}] with ID {1} has status [{2}]'
                  .format(self.name, self.container.short_id, self.container.status))
        print('Use docker ps to monitor container status')
        print('Log files are located in {0}'.format(os.path.join(self.workspace.path, 'store', 'log')))

    def _determine_flask_mode(self, use_dev_env):
        if self.workspace.manifest.uses_flask:
            return 'development' if use_dev_env else 'production'
        return None

    def _determine_memory_limit(self):
        memory_limit = self.workspace.manifest.extract_memory_limit()
        print('Setting memory limit {0}MB'.format(memory_limit))
        return '{0}m'.format(memory_limit)

    def _build_requested_port_mappings(self, flask_host_port):
        port_mappings = {}
        manifest = self.workspace.manifest
        if manifest.uses_flask:
            port_mappings['5000/tcp'] = flask_host_port
        services = manifest.extract_named_services()
        for service in services:
            if service.port:
                if service.port == 5000 and manifest.uses_flask:
                    print('Service {0} will share port 5000 with Flask'.format(service.name))
                else:
                    # To make Docker assign a host port, use None as the map to-value.
                    # https://docker-py.readthedocs.io/en/stable/containers.html
                    port_mappings['{0}/tcp'.format(str(service.port))] = None
                    print('Service {0} will use port {1}'.format(service.name, service.port))
            else:
                print('Service definition {0} does not include a port'.format(service.name))
        return port_mappings

    def retrieve_assigned_port_mappings(self):
        assigned_port_mappings = {}
        for container_port, host_settings in self.container.ports.items():
            assigned_port_mappings[container_port] = host_settings[0]['HostPort']
        # Sort the results by host port.
        return dict(sorted(assigned_port_mappings.items(), key=lambda x: x[1]))

    def remove(self):
        print('Removing container [{0}]'.format(self.name))
        self.docker.remove_container(self.container)
        print('Container [{0}] removal completed successfully'.format(self.name))
