#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# Copyright (c) 2024 Haofan Zheng
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
###


import unittest

from ModularDNS.ModuleManagerLoader import MODULE_MGR

from ModularDNS.Downstream.Handler import DownstreamHandler

import NetRepeater.DNS.ModuleManagerLoader

from NetRepeater.DNS.NetRepeaterMod import ServerManagerMod


class TestModuleManagerLoaders(unittest.TestCase):

	def setUp(self):
		pass

	def tearDown(self):
		pass

	def test_DNS_ModuleManagerLoader_01RegisterAndGetModule(self):
		self.assertEqual(
			MODULE_MGR.GetModule('NetRepeater.ServerManagerMod'),
			ServerManagerMod
		)

		self.assertTrue(
			issubclass(
				MODULE_MGR.GetModule('NetRepeater.ServerManagerMod'),
				DownstreamHandler
			)
		)

		with self.assertRaises(KeyError):
			MODULE_MGR.GetModule('SomethingNotExists')

		with self.assertRaises(KeyError):
			MODULE_MGR.GetModule('Downstream')

		with self.assertRaises(KeyError):
			MODULE_MGR.GetModule('Downstream.')

		with self.assertRaises(KeyError):
			MODULE_MGR.GetModule('Downstream.SomethingNotExists')

