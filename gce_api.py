#!/usr/bin/python
# Copyright 2013 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Module to provide Google Client API wrapper for Google Compute Engine."""


import logging
import os
import os.path
import time

import apiclient.discovery
import httplib2

from oauth2client.client import OAuth2WebServerFlow
import oauth2client.file
import oauth2client.tools


class ResourceZoning(object):
  """Constants to indicate which zone type the resource belongs to."""
  NONE = 0
  GLOBAL = 1
  ZONE = 2


class GceApi(object):
  """Google Client API wrapper for Google Compute Engine."""

  COMPUTE_ENGINE_SCOPE = 'https://www.googleapis.com/auth/compute'
  COMPUTE_ENGINE_API_VERSION = 'v1'
  COMPUTE_ENGINE_IMAGE_PROJECT = {
      'debian-7-wheezy-v20131120': 'debian-cloud',
  }

  WAIT_INTERVAL = 3
  MAX_WAIT_TIMES = 100

  def __init__(self, name, client_id, client_secret, project, zone):
    """Constructor.

    Args:
      name: Name of the user of the class.  Used for credentials filename.
      client_id: Client ID of the user of the class.
      client_secret: Client secret of the user of the class.
      project: Project ID.
      zone: Zone name, e.g. 'us-east-a'
    """
    self._name = name
    self._client_id = client_id
    self._client_secret = client_secret
    self._project = project
    self._zone = zone

  def GetApi(self):
    """Does OAuth2 authorization and prepare Google Compute Engine API.

    Since access key may expire at any moment, call the funciton every time
    making API call.

    Returns:
      Google Client API object for Google Compute Engine.
    """
    # First, check local file for credentials.
    homedir = os.environ['HOME']
    storage = oauth2client.file.Storage(
        os.path.join(homedir, '.%s.credentials' % self._name))
    credentials = storage.get()

    if not credentials or credentials.invalid:
      # If local credentials are not valid, do OAuth2 dance.
      flow = OAuth2WebServerFlow(self._client_id, self._client_secret,
                                 self.COMPUTE_ENGINE_SCOPE)
      credentials = oauth2client.tools.run(flow, storage)

    # Set up http with the credentials.
    authorized_http = credentials.authorize(httplib2.Http())
    return apiclient.discovery.build(
        'compute', self.COMPUTE_ENGINE_API_VERSION, http=authorized_http)

  @staticmethod
  def IsNotFoundError(http_error):
    """Checks if HttpError reason was 'not found'.

    Args:
      http_error: HttpError
    Returns:
      True if the error reason was 'not found', otherwise False.
    """
    return http_error.resp['status'] == '404'

  @classmethod
  def _ResourceUrlFromPath(cls, path):
    """Creates full resource URL from path."""
    return 'https://www.googleapis.com/compute/%s/%s' % (
        cls.COMPUTE_ENGINE_API_VERSION, path)

  def _ResourceUrl(self, resource_type, resource_name,
                   zoning=ResourceZoning.ZONE, project=None):
    """Creates URL to indicate Google Compute Engine resource.

    Args:
      resource_type: Resource type.
      resource_name: Resource name.
      zoning: Which zone type the resource belongs to.
    Returns:
      URL in string to represent the resource.
    """
    if not project:
      project = self._project

    if zoning == ResourceZoning.NONE:
      resource_path = 'projects/%s/%s/%s' % (
          project, resource_type, resource_name)
    elif zoning == ResourceZoning.GLOBAL:
      resource_path = 'projects/%s/global/%s/%s' % (
          project, resource_type, resource_name)
    else:
      resource_path = 'projects/%s/zones/%s/%s/%s' % (
          project, self._zone, resource_type, resource_name)

    return self._ResourceUrlFromPath(resource_path)

  def _ResourceProvidedImageUrl(self, image_name):
    """Create URL to indicate Google Compute Engine image resource.

    Args:
      image_name: default image name provided by google e.g. debian-7.
    Returns:
      URL in string to represent the resource.
    """
    if image_name in self.COMPUTE_ENGINE_IMAGE_PROJECT:
      return self._ResourceUrl('images', image_name, ResourceZoning.GLOBAL,
                               self.COMPUTE_ENGINE_IMAGE_PROJECT[image_name])
    else:
      logging.error('Image %s, is not supported', image_name)
      return None

  def _ParseOperation(self, operation, title):
    """Parses operation result and log warnings and errors if any.

    Args:
      operation: Operation object as result of operation.
      title: Title used for log.
    Returns:
      Boolean to indicate whether the operation was successful.
    """
    if 'error' in operation and 'errors' in operation['error']:
      for e in operation['error']['errors']:
        logging.error('%s: %s: %s',
                      title, e.get('code', 'NO ERROR CODE'),
                      e.get('message', 'NO ERROR MESSAGE'))
      return False

    if 'warnings' in operation:
      for w in operation['warnings']:
        logging.warning('%s: %s: %s',
                        title, w.get('code', 'NO WARNING CODE'),
                        w.get('message', 'NO WARNING MESSAGE'))
    return True

  def GetInstance(self, instance_name):
    """Gets instance information.

    Args:
      instance_name: Name of the instance to get information of.
    Returns:
      Google Compute Engine instance resource.  None if error.
      https://developers.google.com/compute/docs/reference/v1beta14/instances
    """
    return self.GetApi().instances().get(
        project=self._project, zone=self._zone,
        instance=instance_name).execute()

  def ListInstances(self, filter_string=None):
    """Lists instances that matches filter condition.

    Format of filter string can be found in the following URL.
    http://developers.google.com/compute/docs/reference/v1beta14/instances/list

    Args:
      filter_string: Filtering condition.
    Returns:
      List of compute#instance.
    """
    result = self.GetApi().instances().list(
        project=self._project, zone=self._zone, filter=filter_string).execute()
    return result.get('items', [])

  def CreateInstance(self, instance_name, machine_type, disk,
                     startup_script='', service_accounts=None,
                     metadata=None):
    """Creates Google Compute Engine instance.

    Args:
      instance_name: Name of the new instance.
      machine_type: Machine type.  e.g. 'n1-standard-2'
      disk: Name of the persistent disk to be used as a boot disk.  The disk
          must preexist in the same zone as the instance.
      startup_script: Content of start up script to run on the new instance.
      service_accounts: List of scope URLs to give to the instance with
          the service account.
      metadata: Additional key-value pairs in dictionary to add as
          instance metadata.
    Returns:
      Boolean to indicate whether the instance creation was successful.
    """
    params = {
        'kind': 'compute#instance',
        'name': instance_name,
        'zone': self._ResourceUrl('zones', self._zone,
                                  zoning=ResourceZoning.NONE),
        'machineType': self._ResourceUrl('machineTypes', machine_type),
        'disks': [
            {
                'kind': 'compute#attachedDisk',
                'boot': True,
                'source': self._ResourceUrl('disks', disk),
                'deviceName': disk,
                'mode': 'READ_WRITE',
                'type': 'PERSISTENT',
            },
        ],
        'metadata': {
            'kind': 'compute#metadata',
            'items': [
                {
                    'key': 'startup-script',
                    'value': startup_script,
                },
            ],
        },
        'networkInterfaces': [
            {
                'kind': 'compute#instanceNetworkInterface',
                'accessConfigs': [
                    {
                        'kind': 'compute#accessConfig',
                        'type': 'ONE_TO_ONE_NAT',
                        'name': 'External NAT',
                    }
                ],
                'network': self._ResourceUrl('networks', 'default',
                                             zoning=ResourceZoning.GLOBAL)
            },
        ],
        'serviceAccounts': [
            {
                'kind': 'compute#serviceAccount',
                'email': 'default',
                'scopes': service_accounts or [],
            },
        ],
    }

    # Add metadata.
    if metadata:
      for key, value in metadata.items():
        params['metadata']['items'].append({'key': key, 'value': value})

    operation = self.GetApi().instances().insert(
        project=self._project, zone=self._zone, body=params).execute()

    return self._ParseOperation(
        operation, 'Instance creation: %s' % instance_name)

  def CreateInstanceWithNewBootDisk(
      self, instance_name, machine_type, image,
      startup_script='', service_accounts=None, metadata=None):
    """Creates Google Compute Engine instance with newly created boot disk.

    The boot disk is created with the same name as the instance, if the
    disk with the name doesn't exist.  When the disk is ready, an instance is
    created with the disk as its boot disk.

    Args:
      instance_name: Name of the new instance.
      machine_type: Machine type.  e.g. 'n1-standard-2'
      image: Machine image name. e.g. 'debian-7-wheezy-v20131120'
      startup_script: Content of start up script to run on the new instance.
      service_accounts: List of scope URLs to give to the instance with
          the service account.
      metadata: Additional key-value pairs in dictionary to add as
          instance metadata.
    Returns:
      Boolean to indicate whether the instance creation was successful.
    """
    # Use the same disk name as instance name.
    disk_name = instance_name

    # If the boot disk doesn't already exist, create.
    if not self.GetDisk(disk_name):
      if not self.CreateDisk(disk_name, image=image):
        return False

    # Wait until the new persistent disk is READY.
    for _ in xrange(self.MAX_WAIT_TIMES):
      logging.info('Waiting for boot disk %s getting ready...', disk_name)
      time.sleep(self.WAIT_INTERVAL)
      disk = self.GetDisk(disk_name)
      if disk:
        disk_status = disk.get('status', None)
        if disk_status == 'READY' or disk_status == 'RUNNING':
          logging.info('Disk %s created successfully.', disk_name)
          break
    else:
      logging.error('Persistent disk %s creation timed out.', disk_name)
      return False

    return self.CreateInstance(
        instance_name, machine_type, disk_name,
        startup_script, service_accounts, metadata)

  def DeleteInstance(self, instance_name):
    """Deletes Google Compute Engine instance.

    Args:
      instance_name: Name of the instance to delete.
    Returns:
      Boolean to indicate whether the instance deletion was successful.
    """
    operation = self.GetApi().instances().delete(
        project=self._project, zone=self._zone,
        instance=instance_name).execute()

    return self._ParseOperation(
        operation, 'Instance deletion: %s' % instance_name)

  def GetDisk(self, disk_name):
    """Gets persistent disk information.

    Args:
      disk_name: Name of the persistent disk to get information about.
    Returns:
      Google Compute Engine disk resource.  None if not found.
      https://developers.google.com/compute/docs/reference/latest/disks
    Raises:
      HttpError on API error, except for 'resource not found' error.
    """
    try:
      return self.GetApi().disks().get(
          project=self._project, zone=self._zone, disk=disk_name).execute()
    except apiclient.errors.HttpError as e:
      if self.IsNotFoundError(e):
        return None
      raise

  def ListDisks(self, filter_string=None):
    """Lists disks that match filter condition.

    Format of filter string can be found in the following URL.
    https://developers.google.com/compute/docs/reference/latest/disks/list

    Args:
      filter_string: Filtering condition.
    Returns:
      List of compute#disk.
    """
    result = self.GetApi().disks().list(
        project=self._project, zone=self._zone, filter=filter_string).execute()
    return result.get('items', [])

  def CreateDisk(self, disk_name, image, size_gb=10):
    """Creates persistent disk in the zone of this API.

    Args:
      disk_name: Name of the new persistent disk.
      image: Machine image name for the new disk to base upon.
          e.g. 'debian-7-wheezy-v20131120'
      size_gb: Size of the new persistent disk in GB.
    Returns:
      Boolean to indicate whether the disk creation was successful.
    """
    params = {
        'kind': 'compute#disk',
        'sizeGb': '%d' % size_gb,
        'name': disk_name,
    }
    source_image = self. _ResourceProvidedImageUrl(image)
    if not source_image:
      logging.error('CreateDisk must specify a valid image: %s', image)
      return False

    operation = self.GetApi().disks().insert(
        project=self._project, zone=self._zone, body=params,
        sourceImage=source_image).execute()
    return self._ParseOperation(
        operation, 'Disk creation %s' % disk_name)

  def DeleteDisk(self, disk_name):
    """Deletes persistent disk.

    Args:
      disk_name: Name of the persistent disk to delete.
    Returns:
      Boolean to indicate whether the disk deletion was successful.
    """
    operation = self.GetApi().disks().delete(
        project=self._project, zone=self._zone, disk=disk_name).execute()

    return self._ParseOperation(
        operation, 'Disk deletion: %s' % disk_name)

  def CreateFirewall(self, name, allowed):
    """Firewall is created for the default network.

    Firewall created will allow traffic from all sources.  Default network is
    applied to the newly created Compute Engine instance; hence, this firewall
    setting will be applied to the newly created instance as well.

    Args:
      name: The name of the firewall to be created via this method.
      allowed: The ip protocol and port allowed by this new firewall as a list
          of dict type.  See Compute Engine REST API reference for the correct
          syntax.

    Returns:
      A boolean value that indicates whether attempt to insert the firewall was
      made.
    """
    try:
      operation = self.GetApi().firewalls().get(project=self._project,
                                                firewall=name).execute()

      self._ParseOperation(
          operation, 'Firewall retrieval: %s' % name)

      logging.info('Firewall \'%s\' is found. No new firewall is added.', name)
      return True

    except apiclient.errors.HttpError:
      # Cannot find named firewall, go ahead to create it
      params = {
          'sourceRanges': ['0.0.0.0/0'],
          'network': self._ResourceUrl('networks', 'default',
                                       zoning=ResourceZoning.GLOBAL),
          'name': name,
          'allowed': allowed
      }
      operation = self.GetApi().firewalls().insert(
          project=self._project,
          body=params).execute()

      logging.info('Firewall %s is added.', name)

      return self._ParseOperation(
          operation, 'Firewall insertion: %s' % name)
