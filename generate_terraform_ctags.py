#!/usr/bin/env python3
#
#  Copyright 2025 Enrico Tröger
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#

"""
Generate tags files using u-ctags for various Terraform providers.
To be used with Geany or other tools which can process tags files.

Requirements:
- Python3
- pyhcl Python package
- ctags 6.1 or later
- up to 1 GB of disk space or even more depending on the providers configured below
"""

import json
import os
import pathlib
import subprocess

import hcl


WORKING_DIRECTORY = pathlib.Path('/tmp/generate_terraform_ctags')
CTAGS_COMMAND = 'ctags'
TERRAFORM_COMMAND = 'terraform'  # "opentofu" should work as well
TERRAFORM_SCHEMAS_FILENAME = 'providers_schemas.json'
TERRAFORM_SCRIPT_FILENAME = 'generate_schemas_script.tf'

# edit this list as desired
TERRAFORM_PROVIDERS_SCRIPT = '''
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
    }
    azurerm = {
      source  = "hashicorp/azurerm"
    }
    dns = {
      source  = "hashicorp/dns"
    }
    helm = {
      source  = "hashicorp/helm"
    }
    google = {
      source  = "hashicorp/google"
    }
    kubectl = {
      source  = "gavinbunney/kubectl"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
    }
    opentelekomcloud = {
      source  = "opentelekomcloud/opentelekomcloud"
    }
    proxmox = {
      source  = "bpg/proxmox"
    }
  }
}
'''


def _generate_terraform_provider_schemas():
    os.makedirs(WORKING_DIRECTORY, exist_ok=True)
    with open(WORKING_DIRECTORY / 'main.tf', 'w', encoding='utf-8') as tmp_main_tf:
        tmp_main_tf.write(TERRAFORM_PROVIDERS_SCRIPT)

    # init Terraform providers
    subprocess.check_call([TERRAFORM_COMMAND, 'init'], cwd=WORKING_DIRECTORY)

    # extract the schemas
    filename = WORKING_DIRECTORY / TERRAFORM_SCHEMAS_FILENAME
    with open(filename, 'w', encoding='utf-8') as schema_json_file:
        subprocess.check_call(
            [TERRAFORM_COMMAND, 'providers', 'schema', '-json'],
            stdout=schema_json_file,
            cwd=WORKING_DIRECTORY)


def _generate_terraform_tags():
    """
    Parse the provider schema to extract resources and data sources to generate a ctags tags file.
    """
    provider_versions = {}
    with open(WORKING_DIRECTORY / '.terraform.lock.hcl', encoding='utf-8') as terraform_lockfile:
        lockfile_contents = hcl.load(terraform_lockfile)
        for provider_spec, provider_data in lockfile_contents.get('provider', {}).items():
            provider_versions[provider_spec] = provider_data.get('version')

    with open(WORKING_DIRECTORY / TERRAFORM_SCHEMAS_FILENAME, encoding='utf-8') as schema_json_file:
        schemas = json.load(schema_json_file)

    for provider_spec, provider_schema in schemas.get('provider_schemas', {}).items():
        provider_version = provider_versions.get(provider_spec)
        resource_schemas = provider_schema.get('resource_schemas', {}).keys()
        data_source_schemas = provider_schema.get('data_source_schemas', {}).keys()
        _generate_terraform_tags_for_provider(
            provider_spec, provider_version, resource_schemas, data_source_schemas
        )


def _generate_terraform_tags_for_provider(
        provider_spec, provider_version, resource_schemas, data_source_schemas
):
    """
    Generate a Terraform config with all the resources and data sources of the provider
    and parse this config with "ctags" to generate a tags file.
    """
    provider_name = provider_spec.replace('registry.terraform.io/', '').replace('/', '_')
    filename = WORKING_DIRECTORY / TERRAFORM_SCRIPT_FILENAME
    with open(filename, 'w', encoding='utf-8') as terraform_script_file:
        for resource_schema in resource_schemas:
            terraform_script_file.write(f'resource "{resource_schema}" "{resource_schema}" {{}}\n')
        for data_source_schema in data_source_schemas:
            terraform_script_file.write(
                f'data "{data_source_schema}" "{data_source_schema}" {{}}\n'
            )

    provider_version = provider_version or 'unknown'
    output_filename = WORKING_DIRECTORY / f'{provider_name}-{provider_version}.hcl.tags'
    subprocess.check_call(
        [CTAGS_COMMAND, '-f', output_filename, WORKING_DIRECTORY / TERRAFORM_SCRIPT_FILENAME],
        cwd=WORKING_DIRECTORY)

    os.unlink(WORKING_DIRECTORY / TERRAFORM_SCRIPT_FILENAME)


if __name__ == '__main__':
    _generate_terraform_provider_schemas()
    _generate_terraform_tags()
