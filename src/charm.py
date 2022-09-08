#! /usr/bin/env python3

# Copyright 2021 Canonical Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


# import base64
import os
import pwd
import grp

from ops_openstack.plugins.classes import CinderStoragePluginCharm
from ops_openstack.core import charm_class, get_charm_class_for_release
from ops.main import main


DRIVER_ISCSI = "cinder.volume.drivers.huawei.huawei_driver.HuaweiISCSIDriver"
DRIVER_FC = "cinder.volume.drivers.huawei.huawei_driver.HuaweiFCDriver"


def makedir(path, owner='root', group='root', mode=0o555):
    """Create a directory"""
    uid = pwd.getpwnam(owner).pw_uid
    gid = grp.getgrnam(group).gr_gid
    realpath = os.path.abspath(path)
    os.makedirs(realpath, mode)
    os.chown(realpath, uid, gid)


class CinderCharmBase(CinderStoragePluginCharm):

    PACKAGES = ['cinder-common', 'sysfsutils']
    MANDATORY_CONFIG = [
        'protocol',
        'product',
        'username',
        'password',
        'storage-pool',
        'rest-url',
    ]

    # Overriden from the parent. May be set depending on the charm's properties
    stateless = True
    active_active = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def cinder_configuration(self, config):
        # Return the configuration to be set by the principal.
        backend_name = config.get('volume-backend-name',
                                  self.framework.model.app.name)

        # Set huawei_conf_file path
        self.huawei_conf_file = os.path.join(
            "/etc/cinder",
            self.framework.model.app.name,
            "cinder_huawei_conf.xml"
        )

        # Create dir for huawei storage backend driver
        makedir(
            os.path.dirname(self.huawei_conf_file),
            group="cinder",
            mode=0o750
        )

        # Render huawei_conf_file(XML)
        # TODO

        # Set volume_driver
        protocol = self.config.get("protocol").lower()
        if protocol == "iscsi":
            volume_driver = DRIVER_ISCSI
        elif protocol == "fc":
            volume_driver = DRIVER_FC

        # Set all confs
        options = [
            ('volume_driver', volume_driver),
            ('volume_backend_name', backend_name),
            ("cinder_huawei_conf_file", self.huawei_conf_file)
        ]

        if config.get('use-multipath'):
            options.extend([
                ('use_multipath_for_image_xfer', True),
                ('enforce_multipath_for_image_xfer', True)
            ])

        return options


@charm_class
class CinderHuaweiCharm(CinderCharmBase):
    release = 'yoga'


if __name__ == '__main__':
    main(get_charm_class_for_release())
