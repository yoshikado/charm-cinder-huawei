#!/usr/bin/env python3
# Copyright 2021 OpenStack Charmers
# See LICENSE file for licensing details.
#
# Learn more at: https://juju.is/docs/sdk


# import base64
import os
import logging

from ops_openstack.plugins.classes import CinderStoragePluginCharm
from ops.main import main
from ops.model import ActiveStatus
from charmhelpers.core.templating import render
from charmhelpers.core.host import mkdir


logger = logging.getLogger(__name__)

HUAWEI_CNF_FILE = "huawei.xml"
DRIVER_ISCSI = "cinder.volume.drivers.huawei.huawei_driver.HuaweiISCSIDriver"
DRIVER_FC = "cinder.volume.drivers.huawei.huawei_driver.HuaweiFCDriver"


class ProtocolNotImplemented(Exception):
    """Unsupported protocol error."""


class CinderHuaweiCharm(CinderStoragePluginCharm):

    PACKAGES = ['cinder-common', 'sysfsutils']
    MANDATORY_CONFIG = [
        'protocol',
        'product',
        'username',
        'userpassword',
        'storagepool',
        'resturl',
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

        huawei_conf_file = self.create_huawei_conf(config)

        # Set volume_driver
        protocol = config.get("protocol").lower()
        if protocol == "iscsi":
            volume_driver = DRIVER_ISCSI
        elif protocol == "fc":
            volume_driver = DRIVER_FC
        else:
            raise ProtocolNotImplemented(
                "{0} is not an implemented protocol. Please, choose between "
                "`iscsi` and `fc`.".format(protocol)
            )
        logger.debug("Using volume_driver=%s", volume_driver)

        # set multipath
        use_mpath_img_xfer = config.get('use-multipath-for-image-xfer')
        enforce_multipath = config.get('enforce-multipath-image-xfer')

        # Set all confs
        options = [
            ('volume_driver', volume_driver),
            ('volume_backend_name', backend_name),
            ("cinder_huawei_conf_file", huawei_conf_file),
            ('use_multipath_for_image_xfer', use_mpath_img_xfer),
            ('enforce_multipath_for_image_xfer', enforce_multipath)
        ]

        if config.get('hypermetro'):
            config_keys = [
                'storagepool', 'resturl', 'username', 'userpassword',
                'vstorename', 'metrodomain'
            ]
            for k in config_keys:
                if not config.get(k):
                    raise ProtocolNotImplemented(
                        "HyperMetro init error: {0} option is required".format(
                            k
                        )
                    )
            hypermetro_options = ('''storage_pool:{0},
            san_address:{1},
            san_user:{2},
            san_password:{3},
            vstore_name:{4},
            metro_domain:{5},
            metro_sync_completed:True,
            fc_info:'{{'HostName:xxx;ALUA:1;FAILOVERMODE:1;PATHTYPE:0'}}'
            ''').format(
                config.get('storagepool'),
                config.get('resturl'),
                config.get('username'),
                config.get('userpassword'),
                config.get('vstorename'),
                config.get('metrodomain')
            )
            options.append(('hypermetro_device', hypermetro_options))

        return options

    def on_config(self, event):
        config = dict(self.framework.model.config)
        app_name = self.framework.model.app.name
        for relation in self.framework.model.relations.get('storage-backend'):
            self.set_data(relation.data[self.unit], config, app_name)
        self._stored.is_started = True
        self.unit.status = ActiveStatus('Unit is ready')

    def get_huawei_context(self, cfg):
        """Returns a rendered huawer conf file"""
        huaweicontext = {
            'protocol': cfg.get('protocol'),
            'product': cfg.get('product'),
            'username': cfg.get('username'),
            'userpassword': cfg.get('userpassword'),
            'resturl': cfg.get('resturl'),
            'storagepool': cfg.get('storagepool'),
            'luntype': cfg.get('luntype'),
            'luncopyspeed': cfg.get('luncopyspeed'),
            'lunclonemode': cfg.get('lunclonemode'),
            'hypersyncspeed': cfg.get('hypersyncspeed'),
            'iscsidefaulttargetip': cfg.get('iscsidefaulttargetip'),
            'iscsiinitiators': cfg.get('iscsiinitiators'),
            'iscsiportgroupname': cfg.get('iscsiportgroupname'),
            'fchostname': cfg.get('fchostname'),
            'alua': cfg.get('alua'),
            'failovermode': cfg.get('failovermode'),
            'pathtype': cfg.get('pathtype')
        }
        return huaweicontext

    def create_huawei_conf(self, cfg):
        # Set huawei_conf_file path
        huawei_conf_file = os.path.join(
            "/etc/cinder",
            self.framework.model.app.name,
            HUAWEI_CNF_FILE
        )
        # Create dir for huawei storage backend driver
        mkdir(os.path.dirname(huawei_conf_file), owner='cinder')
        # Render huawei_conf_file(XML)
        render(HUAWEI_CNF_FILE, huawei_conf_file,
               self.get_huawei_context(cfg),
               owner='cinder',
               perms=0o644)
        return huawei_conf_file


if __name__ == '__main__':
    main(CinderHuaweiCharm)
