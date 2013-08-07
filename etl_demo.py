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

"""This module automatically instantiate a Compute Engine instance with ETL
tools.

ETL standards for Extract, Transform, and Load which a terminology in data
warehouse paradigm.  It refers to the process when transactional data is
cleansed and transformed before inserted into data warehouse for data analysis
purpose.

One of the installed tool, Knime, enables demonstration of transforming and
ingesting data from ETL tool to BigQuery.  The demonstration can be reproduced
automatically by running this script.  Note that Knime is an open source tool.
More inforation about Knime can be found at http://www.knime.org/knime.
"""



import getpass
import logging
import os
import sys

from gce_api import GceApi

import gflags as flags
from apiclient.errors import HttpError

FLAGS = flags.FLAGS


flags.DEFINE_string(
    'project', 'myproject',
    'Project where Compute Engine and Cloud Storage are managed',
    short_name='p')
flags.DEFINE_string(
    'bucket', 'mystorage',
    'Cloud Storage bucket name where resources for Compute Engine instance '
    'are stored',
    short_name='b')
flags.DEFINE_string(
    'client_id', 'myclientid',
    'Client ID of the user of the project',
    short_name='d')
flags.DEFINE_string(
    'client_secret', 'myclientsecret',
    'Client secret of the user of the project',
    short_name='e')
flags.DEFINE_string(
    'instance_name', 'myinstance',
    'Name of Google Compute Engine to be created',
    short_name='i')
flags.DEFINE_string(
    'startup_script', 'startup-script.sh',
    'Local path of the startup script for Google Compute Engine instance',
    short_name='s')
flags.DEFINE_string(
    'knime', 'knime.tar.gz',
    'Knime zip file name to be downloaded from Cloud Storage by Compute '
    'Engine instance',
    short_name='k')
flags.DEFINE_string(
    'machine_image', 'gcel-12-04-v20130325',
    'Machine image to use for instantiating a Compute Engine virtual machine',
    short_name='m')
flags.DEFINE_string(
    'machine_type', 'n1-standard-4-d',
    'Machine type to use for instantiating a Compute Engine virtual machine',
    short_name='t')
flags.DEFINE_string(
    'zone', 'us-central1-a',
    'Zone where a Compute Engine virtual machine is instantiated',
    short_name='z')
flags.DEFINE_string(
    'log', 'INFO',
    'Set the logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL')


class ComputeManager(object):
  """Represents a manager that manipulates compute resources.

  Utilizes Google APIs Client Library to create and configure a new Compute
  Engine instance
  that is configured to demonstrate the ETL scenario.
  """

  def __init__(self):
    """Instantiate a gce api service."""

    print 'Initialize ComputeManager.'
    self.gce_api = GceApi('etl_demo', FLAGS.client_id,
                          FLAGS.client_secret, FLAGS.project, FLAGS.zone)

  def GetApi(self):
    return self.gce_api

  def StartInstance(self):
    """Start a Compute Engine instance.

    It checks if instance with the same name existed first.  If it exists,
    no instance will be created.

    Returns:
      Boolean to indicate if the specific instance is started.
    """
    try:
      # It checks if instance with the same name existed first.  If it exists,
      # no instance will be created.
      self.GetApi().GetInstance(FLAGS.instance_name)

      print ('Instance \'%s\' is found. Please manually delete the instance '
             'before running this script again, '
             'or use \'--instance_name\' option to create a new instance '
             'with a different name.' % FLAGS.instance_name)
      return True

    except HttpError:
      print ('Adding instance \'%s\'. Use command \'gcutil listinstances\''
             'to check the creation status.' % FLAGS.instance_name)

    service_accounts = [
        'https://www.googleapis.com/auth/devstorage.full_control',
        'https://www.googleapis.com/auth/bigquery'
        ]

    metadata = {
        'startup-storage': FLAGS.bucket,
        'startup-knime-zip': FLAGS.knime,
        'home-user': getpass.getuser()
        }

    return self.GetApi().CreateInstance(FLAGS.instance_name,
                                        FLAGS.machine_type,
                                        FLAGS.machine_image,
                                        open(FLAGS.startup_script).read(),
                                        service_accounts,
                                        metadata)


def main(argv):
  try:
    argv = FLAGS(argv)
    manager = ComputeManager()
    logging.basicConfig(level=FLAGS.log)

    firewall_created = manager.gce_api.CreateFirewall(
        'etl-http2', [{'IPProtocol': 'tcp', 'ports': ['80']}])
    if not firewall_created:
      print 'Firewall is not created successfully.'

    firewall_created = manager.gce_api.CreateFirewall(
        'etl-vnc', [{'IPProtocol': 'tcp', 'ports': ['5900-5999']}])
    if not firewall_created:
      print 'Firewall is not created successfully.'

    if not manager.StartInstance():
      print 'Instance is not created successfully.'

  except flags.FlagsError as e:
    print '%s\nUsage: %s ARGS\n%s' % (e, sys.argv[0], FLAGS)
    sys.exit(1)


if __name__ == '__main__':
  main(sys.argv)
