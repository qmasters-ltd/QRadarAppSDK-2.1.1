# Licensed Materials - Property of IBM
# 5725I71-CC011829
# (C) Copyright IBM Corp. 2015, 2020. All Rights Reserved.
# US Government Users Restricted Rights - Use, duplication or
# disclosure restricted by GSA ADP Schedule Contract with IBM Corp.

import os
import collections
import json
import jsonschema
import uuid
import zipfile
import sdk_util
from sdk_exceptions import SdkManifestException

DEFAULT_MEMORY_LIMIT = 100

MSG_SDK_MANIFEST_FLASK_PORT = \
    ('\nAll apps must expose a /debug endpoint on port 5000 to enable app health checking.'
     '\nYour app does not load Flask and does not define any service on port 5000.')

NamedService = collections.namedtuple('NamedService', ['name', 'port'])

class SdkManifest():
    def __init__(self, manifest_json):
        self.json = manifest_json
        self.uses_flask = SdkManifest._uses_flask(manifest_json)

    @classmethod
    def from_workspace(cls, workspace_path):
        ''' This function is only used at the end of the SdkWorkspace init function
            when the manifest's existence and content have been verified. '''
        with open(os.path.join(workspace_path, 'manifest.json')) as manifest_file:
            return cls(json.load(manifest_file))

    @staticmethod
    def validate_workspace_manifest(manifest_file):
        schema = SdkManifest._read_manifest_schema()
        SdkManifest._validate_manifest(manifest_file, schema)

    @staticmethod
    def validate_zip_manifest(zip_path):
        schema = SdkManifest._read_manifest_schema()
        try:
            with zipfile.ZipFile(zip_path) as zip_file:
                with zip_file.open('manifest.json') as manifest_file:
                    SdkManifest._validate_manifest(manifest_file, schema)
        except zipfile.BadZipfile:
            raise SdkManifestException('{0} is not a valid zip file'.format(zip_path))
        except KeyError:
            raise SdkManifestException('{0} does not contain a manifest.json file'.format(zip_path))

    @staticmethod
    def _read_manifest_schema():
        try:
            with open(sdk_util.build_manifest_schema_path()) as schema_file:
                return schema_file.read()
        except OSError as oe:
            raise SdkManifestException('Unable to perform manifest schema validation: {0}'.format(oe))

    @staticmethod
    def _validate_manifest(manifest_file, schema):
        try:
            manifest_json = json.loads(manifest_file.read(),
                                       object_pairs_hook=SdkManifest._find_duplicate_json_keys)
            error_str = SdkManifest._validate_with_schema(manifest_json, schema)
            error_str += SdkManifest._validate_uuid(manifest_json)
            error_str += SdkManifest._validate_rest_methods(manifest_json)
            error_str += SdkManifest._validate_named_services(manifest_json)
            if error_str:
                raise SdkManifestException('Your manifest.json contains these errors: ' + error_str)
        except (ValueError, TypeError) as err:
            raise SdkManifestException('Your manifest.json is not valid JSON:\n' + str(err))

    @staticmethod
    def _find_duplicate_json_keys(list_of_pairs):
        key_count = collections.Counter(k for k,_ in list_of_pairs)
        duplicate_keys = ', '.join(k for k,v in list(key_count.items()) if v>1)
        if len(duplicate_keys) != 0:
            raise SdkManifestException('Duplicate keys found in manifest.json: {}'.format(duplicate_keys))
        return dict(list_of_pairs)

    @staticmethod
    def _validate_with_schema(manifest_json, schema):
        error_str = ''
        validator = jsonschema.Draft4Validator(json.loads(schema))
        schema_errors = sorted(validator.iter_errors(manifest_json), key=lambda e: e.path)
        if schema_errors:
            for error in schema_errors:
                error_str += '\n'
                for err_thing in error.path:
                    error_str += '[' + str(err_thing) + ']'
                if error.path:
                    error_str += ': '
                error_str += error.message
        return error_str

    @staticmethod
    def _validate_uuid(manifest_json):
        try:
            uuid.UUID(manifest_json['uuid'])
            return ''
        except ValueError:
            return '\nInvalid uuid {0}'.format(manifest_json['uuid'])

    @staticmethod
    def _validate_rest_methods(manifest_json):
        rest_methods = set()
        if 'rest_methods' in manifest_json:
            for method in manifest_json['rest_methods']:
                try:
                    rest_methods.add(method['name'])
                except KeyError:
                    pass

        missing_methods = []
        for field in manifest_json:
            # Only list fields need to be searched.
            if isinstance(manifest_json[field], list):
                for item in manifest_json[field]:
                    if 'rest_method' in item and item['rest_method'] not in rest_methods:
                        missing_methods.append(item['rest_method'])

        error_str = ''
        if missing_methods:
            error_str += '\nThese methods are not defined in the rest_method field: ' + \
                ', '.join(method for method in missing_methods)

        return error_str

    @staticmethod
    def _validate_named_services(manifest_json):
        app_uses_flask = SdkManifest._uses_flask(manifest_json)

        try:
            services = manifest_json['services']
        except KeyError:
            if app_uses_flask:
                return ''
            return MSG_SDK_MANIFEST_FLASK_PORT

        error_str = ''

        service_names = []
        duplicate_service_names = set()
        service_ports = []
        duplicate_service_ports = set()

        for service in services:
            if service['name'] in service_names:
                duplicate_service_names.add(service['name'])
            else:
                service_names.append(service['name'])
            if 'port' in service:
                if service['port'] in service_ports:
                    duplicate_service_ports.add(str(service['port']))
                else:
                    service_ports.append(service['port'])

        if duplicate_service_names:
            error_str += '\nService names must be unique, but these duplicates were found: ' + \
                ', '.join(service_name for service_name in duplicate_service_names)

        if duplicate_service_ports:
            error_str += '\nService ports must be unique, but these duplicates were found: ' + \
                ', '.join(service_port for service_port in duplicate_service_ports)

        if not app_uses_flask:
            if 5000 not in service_ports:
                error_str += MSG_SDK_MANIFEST_FLASK_PORT

        return error_str

    @staticmethod
    def _uses_flask(manifest_json):
        try:
            return manifest_json['load_flask'] == 'true'
        except KeyError:
            return True

    @staticmethod
    def extract_uuid_from_zip_manifest(zip_path):
        try:
            with zipfile.ZipFile(zip_path) as app_zip:
                with app_zip.open('manifest.json') as manifest_file:
                    manifest_json = json.load(manifest_file)
                    return manifest_json['uuid']
        except zipfile.BadZipfile:
            raise SdkManifestException('{0} is not a valid zip file'.format(zip_path))
        except KeyError:
            raise SdkManifestException('{0} does not contain a manifest.json file'.format(zip_path))

    def extract_memory_limit(self):
        try:
            return self.json['resources']['memory']
        except KeyError:
            return DEFAULT_MEMORY_LIMIT

    def extract_named_services(self):
        try:
            services = self.json['services']
        except KeyError:
            return []
        namedservices = []
        for service in services:
            try:
                namedservice = NamedService(service['name'], service['port'])
            except KeyError:
                namedservice = NamedService(service['name'], None)
            namedservices.append(namedservice)
        return namedservices

    def generate_preregistration_request(self):
        return {'manifest': self.json}

    def generate_registration_request(self, local_ip, port_mappings, is_update):
        request_details = {'ip': local_ip,
                           'default_port': int(port_mappings['5000/tcp'])}
        if is_update:
            request_details['manifest'] = self.json
        registration_service_ports = self._generate_registration_service_ports(port_mappings)
        if registration_service_ports:
            request_details['service_ports'] = registration_service_ports
        return request_details

    def _generate_registration_service_ports(self, port_mappings):
        namedservices = self.extract_named_services()
        registration_service_ports = []
        if namedservices:
            for namedservice in namedservices:
                if namedservice.port:
                    try:
                        mapped_service_port = port_mappings[str(namedservice.port) + '/tcp']
                        registration_service_ports.append({'service': namedservice.name,
                                                           'port': int(mapped_service_port)})
                    except (KeyError, ValueError):
                        print('No mapping was found for port {0} in service {1}'.format(
                            namedservice.port, namedservice.name))
        return registration_service_ports

    @staticmethod
    def extract_ports_from_registration_request(request_details):
        ''' Returns string containing comma-separated port numbers sorted in numerical order '''
        ports = [str(request_details['default_port'])]
        if 'service_ports' in request_details:
            for service_entry in request_details['service_ports']:
                port = str(service_entry['port'])
                if port not in ports:
                    ports.append(port)
        return ', '.join(port for port in sorted(ports))
