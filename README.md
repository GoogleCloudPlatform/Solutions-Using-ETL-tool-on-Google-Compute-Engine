# Using ETL tool on Google Compute Engine Readme

## Copyright
Copyright 2013 Google Inc. All Rights Reserved.

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at

[http://www.apache.org/licenses/LICENSE-2.0](http://www.apache.org/licenses/LICENSE-2.0)

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

## Disclaimer
This sample application is not an official Google product.

## Overview
The purpose of "Using ETL tool on Google Compute Engine" is to automatically generate a virtual machine with the right applications installed such that users are enabled to rapidly design, create and execute ETL workflow.  They can then ingest the processed data to Big Query via Google Cloud Storage optionally.  This tool is tested on Google Compute Engine API v1.

## Download Instructions
The "Using ETL tool on Google Compute Engine" utilizes the following script files:

+ etl_demo.py
+ gce_api.py
+ startup_script.sh

After [downloading](https://github.com/GoogleCloudPlatform/solutions-using-etl-tool-on-Google-Compute-Engine/archive/master.zip) the zip file, unzip the package with the following command on your computer (i.e. Mac/Linux):

    unzip solutions-using-etl-tool-on-Google-Compute-Engine.zip

## Operation Guide
This section intends to provide a step by step guide to operate the tool such that you can create an ETL-enabled virtual machine via Google Compute Engine automatically.

### Prerequisites
1. Make sure you have access to a [Google Developers Console](https://cloud.google.com/console) project that have access to both Google Compute Engine and Google Cloud Storage
2. It is assumed that your local computer has both gsutil and gcutil correctly installed and configured.  If you don't, please install [Google Cloud SDK](https://developers.google.com/cloud/sdk/) and follow the installation and set up instructions.
3. Download [KNIME desktop](http://www.knime.org/downloads/knime/linux64) and upload the \*.tar.gz file to a Google Cloud Storage bucket that is referenced by the above Google Cloud Console project.  You will need to provide this Cloud Storage bucket name to "Using ETL tool on Google Compute Engine" later.  You may choose to upload this \*.tar.gz file as knime.tar.gz; otherwise, you will need to specify the name of this package later on when using the "Using ETL tool on Google Compute Engine".

        gsutil cp knime_2.7.4.linux.gtk.x86_64.tar.gz gs://<My_BUCKET>/knime.tar.gz

4. Install the [Google APIs Client Library for Python](https://developers.google.com/api-client-library/python/start/installation) on your local machine

5. Install the Commandline flags module for python [python-gflags](https://code.google.com/p/python-gflags/downloads/list) on your local machine

### Create an ETL-enabled Virtual Machine
1. In command prompt, execute the following command in the directory you extracted the "Using ETL tool on Google Compute Engine".  You need to obtain a client id and secret via the [Google Developers Console](https://cloud.google.com/console).  An installed application client ID is required for the "Using ETL tool on Google Compute Engine".  For more information about obtaining the client ID and secret, see the  Authorizing Request in this [guide](https://developers.google.com/compute/docs/api/python_guide#gettingstarted).

        ./etl_demo.py --project=<Compute Engine enabled project> --bucket=<Cloud Storage bucket name> --client_id=xxxxxxxxxxx.apps.googleusercontent.com --client_secret=xxxxxxxxxxxxx

    For instance, the command looks like the following with project name `google.com:miette` and bucket name `storages`

        ./etl_demo.py --project=”google.com:miette” --bucket=”storages” --client_id=xxxxxxxxxxx.apps.googleusercontent.com --client_secret=xxxxxxxxxxxxx

    For more etl\_demo.py usage information, use ./etl\_demo.py --help to see the most up to date usage manual.  If you did not rename the KNIME package to knime.tar.gz in prerequisite steps, you will need to use --knime option to specify the name of your KNIME package in the command in this step.

    Once this command is issued, you will see command prompt messages that indicate the compute manager is being initialized and a few firewalls are being added to your default Compute Engine network.

2. At this point, the Compute Engine instance may take 5-10 mins to install additional software.  To help you detect if the instance has finished the setup, you can run the following command.

        gsutil ls -l gs://<bucket>/myinstance

    The tool will upload a file with the name of the newly created Compute Engine instance to your Cloud Storage bucket.  By default, the instance name is “myinstance”.  To customize the instance name, you should use --instance_name option in step 1.  If the above command returns an error, that means the setup is not yet completed.  Once the above command returns a reasonable result (i.e. file modified time will be around 5-10 mins after you issue the first command), you can move on to the next step.

3. SSH into the new Compute Engine instance again to establish a VNC session.

        local_machine> gcutil ssh <myinstance>
        myinstance> vnc4server -geometry 1440x900 :1

    Note that if there is no [default project specified for gcutil](https://developers.google.com/compute/docs/gcutil/#project), you will need to execute gcutil ssh with a project option as below:

        local_machine> gcutil --project=<project-id> ssh <myinstance>

    The vnc4server command above will create a new vnc session for you to remote desktop into the instance so that you can use GUI tools.   Read the print out from the above command carefully, it should tell you the session number of your new vnc session as 1.  If this is your first time running the above command in this instance, it will also prompt for a password.  Type any password you want and this password is required when you log on to this vnc session from any remote computer.

4. Now, from any remote computer other than your Compute Engine instance, you can log into Compute Engine instance using VNC remote desktop.  If you are using Ubuntu machine, use the built-in Remote Desktop Viewer (Applications -> Internet).  Make sure to specify to use VNC protocol instead of RDP.  You will need the following information to log into the VNC session: (1) the external IP of the Compute Engine instance.  You can run "gcutil listinstances" in your local machine to get this information (2) the VNC session id.  Again, it is 1.  (3) the password you created in previous step.  If your Ubuntu version does not come with a Remote Desktop Viewer, you can install one from [here](https://apps.ubuntu.com/cat/applications/vinagre/).  Make sure you are compliant to the license term before installing.

    If you use Mac, you can download [Chicken of the VNC](http://sourceforge.net/projects/cotvnc).  Make sure you are compliant to the license term before installing.  The login process is the same as above.

    Some VNC client might not provide a separate input for the VNC session id. If that happens, you can specify the session with the format of <ip>:<vnc session id> i.e. 111.222.333.444:1

5. Use the following commands to navigate your Compute Engine instance remote desktop session via the command window.  All "Using ETL tool on Google Compute Engine" installed software reside in /mnt/ed0 mounted drive.

        To start a chrome browser> /opt/google/chrome/google-chrome &
        To start the KNIME ETL tool> /opt/knime/knime &
        To interact with Cloud Storage> gsutil help

6. Install [Google Cloud SDK](https://developers.google.com/cloud/sdk/) on the Compute Engine instance and follow the installation and set up instructions.

        To interact with Big Query> bq help

### Run a KNIME sample workflow
1. Once you are at the VNC session connecting to the Compute Engine instance, you can fire up KNIME using the following command

        /opt/knime/knime &

2. Once the graphical application is opened, change the workspace to knime/workspace in your home directory and click OK
3. Close the "Welcome to KNIME" splash window
4. In the File menu, click "Import KNIME workflow…"
5. In the pop up windows, under "Source" section, select "Select archive file", then click "Browse..."
6. In the folder browser, navigate to knime/workspace in your home directory and select "Sample\_KNIME\_Project.zip", click OK. Click "Finish" to close the import window.
7. In the KNIME Explorer window, open "Local (Local Workspace)"
8. Double click on "Sample\_KNIME\_Project" in the project explorer on the top left corner, the workflow should be opened.
9. Update the file location for all the CSV Reader and Writer nodes. On the workflow/graph, right click on the CSV Reader and Writer nodes and select "Configure...". Select Browse and select the corresponding CSV file in the knime/workspace/Sample_KNIME_Project directory in your home directory.
10. Select any of the CSV Reader node and execute the selected node by click on the "Run" button.
11. Navigate the workflow/graph until you find the "Interactive Table" node.  Execute the selected node. Right click on the node and select "View: Table View".  You will see a pop up table showing the final workflow result in table format.
12. You can experiment with the workflow and re-execute it.  To learn more about how to use the KNIME tool, please see [the documentation](http://tech.knime.org/workbench).

## Clean up the VNC session and Compute Engine instance
1. You can re-login to the Compute Engine instance vnc session anytime.  After you are done with the vnc session, you should execute the following command to kill the vnc session.

        myinstance> vnc4server -kill :1

2. For any items you created in the Compute Engine instance, it is highly recommended that you upload them to Cloud Storage using gsutil to persist the data. Make sure you periodically upload any valuable data to Cloud Storage. An alternative option is to mount [persistent disk](https://developers.google.com/compute/docs/disks#persistentdisks) to the Compute Engine instance.
3. Finally, when you no longer need the Compute Engine instance, you can delete the instance by issuing the following command.  As long as you persist valuable data from the Compute Engine instance, you can always re-create another ETL-enabled Compute Engine instance via "Using ETL tool on Google Compute Engine".

        local_machine> gcutil deleteinstance myinstance

## Execute the Unit Tests
The "Using ETL tool on Google Compute Engine" comes with unit tests for its modules.  Before you can execute the test, your machine needs to have python mock module installed.  Execute the following command to install mock:

    sudo easy_install mock

1. To verify the correctness of etl_demo.py, execute:

        ./etl_demo_test.py

2. To verify the correctness of gce_api.py, execute:

        ./gce_api_test.py
