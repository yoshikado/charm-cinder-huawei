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
from src.charm import CinderCharmBase
from ops.model import ActiveStatus
from ops.testing import Harness
from unittest.mock import patch


class TestCinderHuaweiCharm(unittest.TestCase):

    def setUp(self):
        self.makedirs = patch('os.makedirs').start()
        self.getgrnam = patch('grp.getgrnam').start()
        self.chown = patch('os.chown').start()
        self.harness = Harness(CinderCharmBase)
        self.addCleanup(self.harness.cleanup)
        self.harness.begin()
        self.harness.set_leader(True)
        backend = self.harness.add_relation('storage-backend', 'cinder')
        test_config = {
            'protocol': 'iscsi',
            'product': 'Dorado',
            'username': 'username',
            'password': 'password',
            'storage-pool': 'storagepool',
            'rest-url': 'https://example.com:8088/deviceManager/rest/',
            'volume-backend-name': 'test'
        }
        self.harness.update_config(test_config)
        self.harness.add_relation_unit(backend, 'cinder/0')

    def test_cinder_base(self):
        self.assertEqual(
            self.harness.framework.model.app.name,
            'cinder-huawei')
        # Test that charm is active upon installation.
        self.harness.update_config({})
        self.assertTrue(isinstance(
            self.harness.model.unit.status, ActiveStatus))

    def test_multipath_config(self):
        self.harness.update_config({'use-multipath': True})
        conf = dict(self.harness.charm.cinder_configuration(
            dict(self.harness.model.config)))
        self.assertEqual(conf['volume_backend_name'], 'test')
        self.assertTrue(conf.get('use_multipath_for_image_xfer'))
        self.assertTrue(conf.get('enforce_multipath_for_image_xfer'))

    def test_cinder_configuration(self):
        test_config = {
            'protocol': 'iscsi',
            'product': 'Dorado',
            'username': 'username',
            'password': 'password',
            'storage-pool': 'storagepool',
            'rest-url': 'https://example.com:8088/deviceManager/rest/',
            'volume-backend-name': 'test'
        }
        config = self.harness.model.config

        self.harness.update_config(test_config)

        self.assertTrue(isinstance(
            self.harness.model.unit.status, ActiveStatus))
        for k in test_config:
            self.assertEqual(test_config[k], config[k])
