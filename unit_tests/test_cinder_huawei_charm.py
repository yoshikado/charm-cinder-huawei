# Copyright 2016 Canonical Ltd
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

import unittest
from src.charm import CinderHuaweiCharm
from ops.model import (
    ActiveStatus,
    BlockedStatus,
)
from ops.testing import Harness
from unittest.mock import patch

TEST_XML_PATH = "/etc/cinder/cinder-huawei/cinder_huawei_conf.xml"


class TestCinderHuaweiCharm(unittest.TestCase):

    def setUp(self):
        self.harness = Harness(CinderHuaweiCharm)
        self.addCleanup(self.harness.cleanup)
        self.harness.begin()
        self.harness.set_leader(True)
        backend = self.harness.add_relation('storage-backend', 'cinder')
        self.harness.add_relation_unit(backend, 'cinder/0')

    def test_cinder_base(self):
        self.assertEqual(
            self.harness.framework.model.app.name,
            'cinder-huawei')
        # Test that charm is blocked because of missing configurations.
        self.harness.update_config({})
        self.assertTrue(isinstance(
            self.harness.model.unit.status, BlockedStatus))

    @patch.object(CinderHuaweiCharm, 'create_huawei_conf')
    def test_multipath_config(self, mock_create_huawei_conf):
        self.harness.update_config({'use-multipath': True})
        mock_create_huawei_conf.return_value = TEST_XML_PATH
        conf = dict(self.harness.charm.cinder_configuration(
            dict(self.harness.model.config)))
        self.assertTrue(conf.get('use_multipath_for_image_xfer'))
        self.assertTrue(conf.get('enforce_multipath_for_image_xfer'))

    @patch.object(CinderHuaweiCharm, 'create_huawei_conf')
    def test_cinder_configuration(self, mock_create_huawei_conf):
        mock_create_huawei_conf.return_value = TEST_XML_PATH
        test_config = {
            'protocol': 'iscsi',
            'product': 'Dorado',
            'username': 'myuser',
            'password': 'mypassword',
            'storage-pool': 'mystoragepool',
            'rest-url': 'https://example.com:8088/deviceManager/rest/',
            'volume-backend-name': 'huawei_dorado_iscsi',
        }
        self.harness.model.config
        self.harness.update_config(test_config)
        conf = dict(self.harness.charm.cinder_configuration(
            dict(self.harness.model.config)))
        self.assertTrue(isinstance(
            self.harness.model.unit.status, ActiveStatus))
        self.assertEqual(conf['volume_backend_name'], 'huawei_dorado_iscsi')
        self.assertEqual(
            conf['volume_driver'],
            'cinder.volume.drivers.huawei.huawei_driver.HuaweiISCSIDriver'
        )
        self.assertEqual(
            conf['cinder_huawei_conf_file'],
            TEST_XML_PATH
        )

    @patch.object(CinderHuaweiCharm, 'create_huawei_conf')
    def test_cinder_configuration_fc(self, mock_create_huawei_conf):
        mock_create_huawei_conf.return_value = TEST_XML_PATH
        test_config = {
            'protocol': 'fc',
            'product': 'Dorado',
            'username': 'myuser',
            'password': 'mypassword',
            'storage-pool': 'mystoragepool',
            'rest-url': 'https://example.com:8088/deviceManager/rest/',
            'volume-backend-name': 'huawei_dorado_fc',
        }
        self.harness.model.config
        self.harness.update_config(test_config)
        conf = dict(self.harness.charm.cinder_configuration(
            dict(self.harness.model.config)))
        self.assertTrue(isinstance(
            self.harness.model.unit.status, ActiveStatus))
        self.assertEqual(conf['volume_backend_name'], 'huawei_dorado_fc')
        self.assertEqual(
            conf['volume_driver'],
            'cinder.volume.drivers.huawei.huawei_driver.HuaweiFCDriver'
        )
        self.assertEqual(
            conf['cinder_huawei_conf_file'],
            TEST_XML_PATH
        )
