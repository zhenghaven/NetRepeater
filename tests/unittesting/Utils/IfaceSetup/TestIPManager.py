#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# Copyright (c) 2024 Haofan Zheng
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
###


import ipaddress
import logging
import unittest

from NetRepeater.Utils.IfaceSetup.IPManager import CreateIPManager


class TestIPManager(unittest.TestCase):

	def setUp(self):
		pass

	def tearDown(self):
		pass

	def test_Utils_IfaceSetup_IPManager_01AddAndRemoveIP(self):
		logging.getLogger().info('')

		ipMgr = CreateIPManager(
			mode='linux-dry-run',
			ipAndNet=ipaddress.ip_interface('::1/128'),
			iface='eth0',
		)

		ipMgr.AddIP(waitConfirm=False)
		self.assertTrue(ipMgr.HasIPAdded())

		ipMgr.RemoveIP(waitConfirm=False)
		self.assertFalse(ipMgr.HasIPAdded())

		ipMgr.AddIP(waitConfirm=True)
		self.assertTrue(ipMgr.HasIPAdded())

		ipMgr.RemoveIP(waitConfirm=True)
		self.assertFalse(ipMgr.HasIPAdded())

	def test_Utils_IfaceSetup_IPManager_02BindToInvalidIP(self):
		logging.getLogger().info('')

		ipMgr = CreateIPManager(
			mode='linux-dry-run',
			ipAndNet=ipaddress.ip_interface('fd00:0123:4567:89ab:cdef:ffff:0000:1/128'),
			iface='eth0',
		)

		with self.assertRaises(TimeoutError):
			ipMgr.WaitBindable(timeout=0.5)

