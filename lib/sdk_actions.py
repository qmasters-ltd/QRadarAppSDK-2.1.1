# Licensed Materials - Property of IBM
# 5725I71-CC011829
# (C) Copyright IBM Corp. 2015, 2020. All Rights Reserved.
# US Government Users Restricted Rights - Use, duplication or
# disclosure restricted by GSA ADP Schedule Contract with IBM Corp.

import os
import sys
import sdk_certificates
from sdk_container import SdkContainer
from sdk_developerapp import SdkDeveloperApp
from sdk_docker import SdkDockerClient
from sdk_image import SdkImage
from sdk_manifest import SdkManifest
import sdk_package
from sdk_rest import SdkRestClient
from sdk_server import SdkServer
import sdk_util
from sdk_workspace import SdkWorkspace
from sdk_exceptions import (SdkContainerError, SdkFatalError,
                            SdkServerSslError, SdkWorkspaceError)

# SDK action entry points

def create_workspace(qapp_args):
    try:
        workspace = SdkWorkspace(qapp_args.workspace, check_dir_exists=False, check_content=False)
        workspace.populate_from_template(qapp_args.key)
    except (OSError, SdkFatalError) as err:
        _handle_fatal_error(err)

def package(qapp_args):
    try:
        workspace = SdkWorkspace(qapp_args.workspace, check_dir_name=False)
        sdk_package.create_zip(workspace, qapp_args.package)
    except (ValueError, OSError, SdkFatalError) as err:
        _handle_fatal_error(err)

def build_image(qapp_args):
    try:
        workspace = SdkWorkspace(qapp_args.workspace)
        docker = SdkDockerClient()
        image = SdkImage(docker, workspace)
        image.build()
    except (ValueError, OSError, SdkFatalError) as err:
        _handle_fatal_error(err)

def run_app(qapp_args):
    try:
        workspace = SdkWorkspace(qapp_args.workspace, check_secret_uuid=True)
        docker = SdkDockerClient()

        dev_app_instance_id = None
        qconsole = None
        if qapp_args.qradar_console:
            qconsole = qapp_args.qradar_console
            sdk_certificates.check_host_bundle_status(qconsole)
            dev_app_instance_id = workspace.retrieve_dev_app_instance_id(qconsole)

        image = SdkImage(docker, workspace)
        if not image.is_in_registry():
            image.build()

        container = SdkContainer(docker, workspace, running=False)
        container.run(qapp_args.host_port, qapp_args.show_logs,
                      qapp_args.use_dev_env, qconsole, dev_app_instance_id)

    except (ValueError, OSError, SdkFatalError) as err:
        _handle_fatal_error(err)

def clean(qapp_args):
    try:
        workspace = SdkWorkspace(qapp_args.workspace, check_content=False)
        docker = SdkDockerClient()

        lookup_error = False
        try:
            container = SdkContainer(docker, workspace)
        except SdkContainerError:
            lookup_error = True
        else:
            container.remove()

        if qapp_args.image_remove:
            image = SdkImage(docker, workspace)
            if image.is_in_registry():
                image.remove()
            else:
                lookup_error = True

    except (ValueError, OSError, SdkFatalError) as err:
        _handle_fatal_error(err)

    if lookup_error:
        sys.exit(1)

def server_details(qapp_args):
    try:
        server = SdkServer.resolve(qapp_args, print_details=True)
        sdk_certificates.verify_certificate_bundle(server.qserver_ip)
    except SdkFatalError as sfe:
        _handle_fatal_error(sfe)

def preregister(qapp_args):
    try:
        workspace = SdkWorkspace(qapp_args.workspace)
        server = SdkServer.resolve(qapp_args)
        rest_client = _create_rest_client(server)

        server_registered_apps = rest_client.retrieve_development_apps()
        existing_app = SdkDeveloperApp.from_workspace(
            workspace, server.qserver_ip, server_registered_apps)

        if existing_app:
            raise SdkWorkspaceError('An app is already {0} for workspace [{1}] on server {2}'
                                    .format(existing_app.state(), workspace.name, server.qserver_ip))

        preregistration_request = workspace.manifest.generate_preregistration_request()
        response_json = rest_client.preregister_development_app(preregistration_request, workspace)

        app = SdkDeveloperApp.from_api_response(response_json, server.qserver_ip)
        app.save(workspace)

    except SdkServerSslError as sse:
        _handle_ssl_error(sse, server)
    except (ValueError, OSError, SdkFatalError) as err:
        _handle_fatal_error(err)

def register(qapp_args):
    # pylint: disable=too-many-locals
    try:
        workspace = SdkWorkspace(qapp_args.workspace)
        server = SdkServer.resolve(qapp_args)
        rest_client = _create_rest_client(server)

        server_registered_apps = rest_client.retrieve_development_apps()
        existing_app = SdkDeveloperApp.from_workspace(
            workspace, server.qserver_ip, server_registered_apps)

        if not existing_app:
            raise SdkWorkspaceError(
                'You must preregister your app on server {0} before attempting to register it'
                .format(server.qserver_ip))

        try:
            container = SdkContainer(SdkDockerClient(), workspace)
        except SdkContainerError:
            raise SdkWorkspaceError('An app must be running locally before it can be registered.')

        assigned_port_mappings = container.retrieve_assigned_port_mappings()

        if existing_app.is_preregistered():
            endpoint = rest_client.register_development_app
            is_update = False
        else:
            endpoint = rest_client.update_development_app
            is_update = True

        registration_request = workspace.manifest.generate_registration_request(
            qapp_args.local_ip, assigned_port_mappings, is_update)

        register_response_json = endpoint(existing_app.definition_id, registration_request, workspace)

        app = SdkDeveloperApp.from_api_response(register_response_json, server.qserver_ip)
        app.save(workspace)

    except SdkServerSslError as sse:
        _handle_ssl_error(sse, server)
    except (ValueError, OSError, SdkFatalError) as err:
        _handle_fatal_error(err)

def deregister(qapp_args):
    try:
        workspace = SdkWorkspace(qapp_args.workspace, check_dir_name=False, check_content=False)
        server = SdkServer.resolve(qapp_args)
        rest_client = _create_rest_client(server)

        server_registered_apps = rest_client.retrieve_development_apps()
        existing_app = SdkDeveloperApp.from_workspace(
            workspace, server.qserver_ip, server_registered_apps)

        if existing_app:
            rest_client.deregister_development_app(existing_app.definition_id, workspace)
        else:
            print('No registered app was found for workspace [{0}] and server {1}'
                  .format(os.path.basename(workspace.path), server.qserver_ip))

        SdkDeveloperApp.remove(workspace, server.qserver_ip)

        if not existing_app:
            sys.exit(1)

    except SdkServerSslError as sse:
        _handle_ssl_error(sse, server)
    except (ValueError, OSError, SdkFatalError) as err:
        _handle_fatal_error(err)

def check_app_status(qapp_args):
    try:
        server = SdkServer.resolve(qapp_args)
        rest_client = _create_rest_client(server)
        rest_client.display_app_status(qapp_args.application_id)
    except SdkServerSslError as sse:
        _handle_ssl_error(sse, server)
    except SdkFatalError as sfe:
        _handle_fatal_error(sfe)

def deploy(qapp_args):
    try:
        SdkManifest.validate_zip_manifest(qapp_args.package)
        server = SdkServer.resolve(qapp_args)
        rest_client = _create_rest_client(server)
        rest_client.deploy_app(qapp_args.package, qapp_args.auth_user, qapp_args.upload_timeout)
    except SdkServerSslError as sse:
        _handle_ssl_error(sse, server)
    except (KeyError, ValueError, SdkFatalError, OSError) as err:
        _handle_fatal_error(err)

def authorize(qapp_args):
    try:
        server = SdkServer.resolve(qapp_args)
        rest_client = _create_rest_client(server)
        rest_client.authorize_app(qapp_args.application_id, qapp_args.auth_user)
    except SdkServerSslError as sse:
        _handle_ssl_error(sse, server)
    except SdkFatalError as sfe:
        _handle_fatal_error(sfe)

def cancel_app_install(qapp_args):
    try:
        server = SdkServer.resolve(qapp_args)
        rest_client = _create_rest_client(server)
        rest_client.cancel_install(qapp_args.application_id)
    except SdkServerSslError as sse:
        _handle_ssl_error(sse, server)
    except SdkFatalError as sfe:
        _handle_fatal_error(sfe)

def delete_app(qapp_args):
    try:
        server = SdkServer.resolve(qapp_args)
        rest_client = _create_rest_client(server)
        rest_client.delete_app(qapp_args.application_id)
    except SdkServerSslError as sse:
        _handle_ssl_error(sse, server)
    except SdkFatalError as sfe:
        _handle_fatal_error(sfe)

# Utility functions

def _create_rest_client(server):
    return SdkRestClient(server.qserver_ip, server.quser_id)

def _handle_ssl_error(ssl_error, server):
    print(ssl_error)
    print('Removing invalid certificate bundle for server {0}'.format(server.qserver_ip))
    sdk_util.remove_host_config(server.qserver_ip)
    print('To replace the certificate bundle, retry this action or use the qapp server action')
    sys.exit(1)

def _handle_fatal_error(sdk_error):
    print(sdk_util.strip_errno_prefix(str(sdk_error)))
    sys.exit(1)
