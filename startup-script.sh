#!/bin/bash -v
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
#
# This script installs components required for running GUI desktop on GCE
# instance, Extract Transform & Load tools and tools enabling BigQuery data
# ingestion.

GCE_METADATA_URL=http://metadata.google.internal/0.1/meta-data/attributes

STORAGE_BUCKET=$(curl ${GCE_METADATA_URL}/startup-storage)
KNIME_ZIP=$(curl ${GCE_METADATA_URL}/startup-knime-zip)
HOME_USER=$(curl ${GCE_METADATA_URL}/home-user)

# Format and mount the ephemeral drive
MOUNT_DRIVE=/mnt/ed0
mkdir ${MOUNT_DRIVE}

DISK_DEVICE=/dev/disk/by-id/google-ephemeral-disk-0
/usr/share/google/safe_format_and_mount ${DISK_DEVICE} ${MOUNT_DRIVE}

# Update the mounted drive permission and change directory
chmod 755 ${MOUNT_DRIVE}
cd ${MOUNT_DRIVE}

# Get updates
apt-get update

# Install kde-desktop
apt-get -y install kde-plasma-desktop

# Install vnc4server
apt-get -y install vnc4server
apt-get -y install xterm

# Install knime (assume it's already in GCS)
gsutil cp gs://${STORAGE_BUCKET}/${KNIME_ZIP} .
KNIME_HOME=${MOUNT_DRIVE}/knime
mkdir ${KNIME_HOME}
tar -xf ${KNIME_ZIP} -C ${KNIME_HOME} --strip-components=1

# Install httplib2 for BQ tool
curl -O http://httplib2.googlecode.com/files/httplib2-0.8.tar.gz
HTTPLIB2_HOME=${MOUNT_DRIVE}/httplib2
mkdir ${HTTPLIB2_HOME}
tar -xfz httplib2*.tar.gz -C ${HTTPLIB2_HOME} --strip-components=1
python ${HTTPLIB2_HOME}/setup.py install

curl -O \
    http://google-bigquery-tools.googlecode.com/files/bigquery-2.0.13.tar.gz
BQ_HOME=${MOUNT_DRIVE}/bigquery
mkdir ${BQ_HOME}
tar -xf bigquery*.tar.gz -C ${BQ_HOME} --strip-components=1
ln -s ${BQ_HOME}/bq.py /usr/bin/bq
chmod -R a+x+r ${BQ_HOME}

# Install chrome browser
curl -O \
    https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
dpkg -i ./google-chrome*.deb
apt-get -f -y install

# Copy knime sample
gsutil cp gs://storage-uploads/sample/Sample_KNIME_Project.zip .

# Notify the script is done
date | gsutil cp - gs://${STORAGE_BUCKET}/$(uname -n)

# Set up xstartup for vnc
VNC_PATH=/home/${HOME_USER}/.vnc
mkdir -p ${VNC_PATH}
gsutil cp gs://storage-uploads/sample/xstartup ${VNC_PATH}
chown ${HOME_USER} ${VNC_PATH}
chown ${HOME_USER} ${VNC_PATH}/xstartup
chmod 755 ${VNC_PATH}/xstartup
