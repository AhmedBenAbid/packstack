# -*- coding: utf-8 -*-
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
This module provides all the predefined variables.
"""

import os
import sys
import datetime
import tempfile

from .utils import get_current_user


APP_NAME = "Packstack"

FILE_YUM_VERSION_LOCK = "/etc/yum/pluginconf.d/versionlock.list"

PACKSTACK_VAR_DIR = "/var/tmp/packstack"
try:
    os.mkdir(PACKSTACK_VAR_DIR, 0o700)
except OSError:
    # directory is already created, check ownership
    stat = os.stat(PACKSTACK_VAR_DIR)
    if stat.st_uid == 0 and os.getuid() != stat.st_uid:
        print ('%s is already created and owned by root. Please change '
               'ownership and try again.' % PACKSTACK_VAR_DIR)
        sys.exit(1)
finally:
    uid, gid = get_current_user()

    if uid != 0 and os.getuid() == 0:
        try:
            os.chown(PACKSTACK_VAR_DIR, uid, gid)
        except Exception as ex:
            print ('Unable to change owner of %s. Please fix ownership '
                   'manually and try again.' % PACKSTACK_VAR_DIR)
            sys.exit(1)

_tmpdirprefix = datetime.datetime.now().strftime('%Y%m%d-%H%M%S-')
VAR_DIR = tempfile.mkdtemp(prefix=_tmpdirprefix, dir=PACKSTACK_VAR_DIR)
DIR_LOG = VAR_DIR
FILE_LOG = 'openstack-setup.log'
PUPPET_MANIFEST_RELATIVE = "manifests"
PUPPET_MANIFEST_DIR = os.path.join(VAR_DIR, PUPPET_MANIFEST_RELATIVE)
HIERADATA_FILE_RELATIVE = "hieradata"
HIERADATA_DIR = os.path.join(VAR_DIR, HIERADATA_FILE_RELATIVE)

FILE_INSTALLER_LOG = "setup.log"

DIR_PROJECT_DIR = os.environ.get('INSTALLER_PROJECT_DIR', os.path.join(os.getcwd(), 'packstack'))
DIR_PLUGINS = os.path.join(DIR_PROJECT_DIR, "plugins")
DIR_MODULES = os.path.join(DIR_PROJECT_DIR, "modules")

EXEC_RPM = "rpm"
EXEC_SEMANAGE = "semanage"
EXEC_NSLOOKUP = "nslookup"
EXEC_CHKCONFIG = "chkconfig"
EXEC_SERVICE = "service"
EXEC_IP = "ip"

# space len size for color print
SPACE_LEN = 70
