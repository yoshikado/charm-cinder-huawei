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

        # Set all confs
        options = [
            ('volume_driver', volume_driver),
            ('volume_backend_name', backend_name),
            ("cinder_huawei_conf_file", huawei_conf_file)
        ]

        if config.get('use-multipath'):
            options.extend([
                ('use_multipath_for_image_xfer', True),
                ('enforce_multipath_for_image_xfer', True)
            ])

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
            'password': cfg.get('password'),
            'rest_url': cfg.get('rest-url'),
            'storage_pool': cfg.get('storage-pool'),
            'luntype': cfg.get('luntype'),
            'default_targetip': cfg.get('default-targetip'),
            'initiator_name': cfg.get('initiator-name'),
            'target_portgroup': cfg.get('target-portgroup'),
            'fc_hostname': cfg.get('fc-hostname'),
            'alua': cfg.get('alua'),
            'failovermode': cfg.get('failover-mode'),
            'pathtype': cfg.get('path-type')
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
