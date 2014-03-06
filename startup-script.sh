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

GCE_METADATA_URL=http://metadata/computeMetadata/v1/instance/attributes
GCE_METADATA_HDR="X-Google-Metadata-Request: True"

STORAGE_BUCKET=$(curl ${GCE_METADATA_URL}/startup-storage -H "${GCE_METADATA_HDR}")
KNIME_ZIP=$(curl ${GCE_METADATA_URL}/startup-knime-zip -H "${GCE_METADATA_HDR}")
HOME_USER=$(curl ${GCE_METADATA_URL}/home-user -H "${GCE_METADATA_HDR}")

# Get updates
apt-get update

# Install kde-desktop
# The installation prompts the user to enter the keyboard configuration
# and the language setting. The DEBIAN_FRONTEND=noninteractive
# turns it off and instructus the installer to use the default setting.
DEBIAN_FRONTEND=noninteractive apt-get -y install kde-plasma-desktop

# Install vnc4server
apt-get -y install vnc4server
apt-get -y install xterm

# Install the C version of the crcmod.
# gsutil cp automatically splits up large files and upload
# them in parallel and then compose them back. The composite object
# uses CRC for checksum. The default crcmod is a python implementation
# and is slow. gsutil prefers a native C version.
# Note: This startup script is for Debian only.
apt-get -y install gcc python-dev python-setuptools
easy_install -U pip
pip uninstall crcmod
pip install -U crcmod

# Install knime (assume it's already in GCS)
gsutil cp gs://${STORAGE_BUCKET}/${KNIME_ZIP} .
KNIME_HOME=/opt/knime
mkdir ${KNIME_HOME}
tar -xf ${KNIME_ZIP} -C ${KNIME_HOME} --strip-components=1

# Copy knime sample into user's directory
USER_KNIME_DIR=$(sudo -u $HOME_USER bash -c 'echo $HOME')/knime
mkdir ${USER_KNIME_DIR}
chown ${HOME_USER} ${USER_KNIME_DIR}
mkdir ${USER_KNIME_DIR}/workspace
chown ${HOME_USER} ${USER_KNIME_DIR}/workspace
gsutil cp gs://storage-uploads/sample/Sample_KNIME_Project.zip ${USER_KNIME_DIR}/workspace
chown ${HOME_USER} ${USER_KNIME_DIR}/workspace/Sample_KNIME_Project.zip

# Install chrome browser
curl -O \
    https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
dpkg -i ./google-chrome*.deb
apt-get -f -y install

# Notify the script is done
date | gsutil cp - gs://${STORAGE_BUCKET}/$(uname -n)

# Set up xstartup for vnc
VNC_PATH=/home/${HOME_USER}/.vnc
mkdir -p ${VNC_PATH}
gsutil cp gs://storage-uploads/sample/xstartup ${VNC_PATH}
chown ${HOME_USER} ${VNC_PATH}
chown ${HOME_USER} ${VNC_PATH}/xstartup
chmod 755 ${VNC_PATH}/xstartup
