#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# Copyright (c) 2024 Haofan Zheng
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
###


import unittest

import ipaddress

from NetRepeater.Utils.RandIPGenerator import RandIPGenerator


class TestRandIPGenerator(unittest.TestCase):

	def setUp(self):
		pass

	def tearDown(self):
		pass

	def test_Utils_RandIPGenerator_01GenerateFromInt(self):
		ipGen = RandIPGenerator(ipaddress.ip_network('192.168.1.0/24'))

		ip = ipGen._GenerateFromInt(0x1000000001)
		self.assertEqual(ip, ipaddress.ip_address('192.168.1.1'))

		ip = ipGen._GenerateFromInt(0x1FFFFFFFFF)
		self.assertEqual(ip, ipaddress.ip_address('192.168.1.255'))

		ip = ipGen._GenerateFromInt(0b1010101010101010101010101010) # 128 + 32 + 8 + 2 = 170
		self.assertEqual(ip, ipaddress.ip_address('192.168.1.170'))

		ip = ipGen._GenerateFromInt(0b0101010101010101010101010101) # 64 + 16 + 4 + 1 = 85
		self.assertEqual(ip, ipaddress.ip_address('192.168.1.85'))

		with self.assertRaises(ValueError):
			ipGen._GenerateFromInt(0x01)


		ipGen = RandIPGenerator(ipaddress.ip_network('192.168.0.0/16'))

		ip = ipGen._GenerateFromInt(0x1000000001)
		self.assertEqual(ip, ipaddress.ip_address('192.168.0.1'))

		ip = ipGen._GenerateFromInt(0x1FFFFFFFFF)
		self.assertEqual(ip, ipaddress.ip_address('192.168.255.255'))

		ip = ipGen._GenerateFromInt(0b1010101010101010101010101010) # 128 + 32 + 8 + 2 = 170
		self.assertEqual(ip, ipaddress.ip_address('192.168.170.170'))

		ip = ipGen._GenerateFromInt(0b0101010101010101010101010101) # 64 + 16 + 4 + 1 = 85
		self.assertEqual(ip, ipaddress.ip_address('192.168.85.85'))

		with self.assertRaises(ValueError):
			ipGen._GenerateFromInt(0x01)


		ipGen = RandIPGenerator(ipaddress.ip_network('fe80::/112'))

		ip = ipGen._GenerateFromInt(0x1000000001)
		self.assertEqual(ip, ipaddress.ip_address('fe80::1'))

		ip = ipGen._GenerateFromInt(0x1FFFFFFFFF)
		self.assertEqual(ip, ipaddress.ip_address('fe80::ffff'))

		ip = ipGen._GenerateFromInt(0b1010101010101010101010101010101010101010)
		self.assertEqual(ip, ipaddress.ip_address('fe80::aaaa'))

		ip = ipGen._GenerateFromInt(0b0101010101010101010101010101010101010101)
		self.assertEqual(ip, ipaddress.ip_address('fe80::5555'))

		with self.assertRaises(ValueError):
			ipGen._GenerateFromInt(0x01)


		ipGen = RandIPGenerator(ipaddress.ip_network('fe80::/96'))

		ip = ipGen._GenerateFromInt(0x1000000001)
		self.assertEqual(ip, ipaddress.ip_address('fe80::1'))

		ip = ipGen._GenerateFromInt(0x1FFFFFFFFF)
		self.assertEqual(ip, ipaddress.ip_address('fe80::ffff:ffff'))

		ip = ipGen._GenerateFromInt(0b1010101010101010101010101010101010101010)
		self.assertEqual(ip, ipaddress.ip_address('fe80::aaaa:aaaa'))

		ip = ipGen._GenerateFromInt(0b0101010101010101010101010101010101010101)
		self.assertEqual(ip, ipaddress.ip_address('fe80::5555:5555'))

		with self.assertRaises(ValueError):
			ipGen._GenerateFromInt(0x01)


	def test_Utils_RandIPGenerator_02GenerateByName(self):
		ipGen = RandIPGenerator(ipaddress.ip_network('fe80::/64'))

		dupList = []
		def _checkDup(ip):
			return ip in dupList

		ip = ipGen.GenerateByNameStr('test', _checkDup, 3)
		self.assertEqual(ip, ipaddress.ip_address('fe80::d15d:6c15:b0f0:a08'))
		dupList.append(ip)

		ip = ipGen.GenerateByNameStr('test', _checkDup, 3)
		self.assertEqual(ip, ipaddress.ip_address('fe80::8527:d1bf:f591:b7a7'))
		dupList.append(ip)

		ip = ipGen.GenerateByNameStr('test', _checkDup, 3)
		self.assertEqual(ip, ipaddress.ip_address('fe80::9455:c9f2:5234:10e6'))
		dupList.append(ip)

		with self.assertRaises(RuntimeError):
			ipGen.GenerateByNameStr('test', _checkDup, 3)

