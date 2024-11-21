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
import socket
import time
import unittest

from typing import List

from NetRepeater.Inbound.TCP import TCP
from NetRepeater.Outbound.TCP import TCPwStaticIPConnector

from ..MockServer import CreateMockTCPServer


class TestTCPServer(unittest.TestCase):

	def setUp(self):
		self.localhostAddrV6 = ipaddress.ip_address('::1')
		self.localhostAfV6 = socket.AF_INET6
		self.localhostAddrV4 = ipaddress.ip_address('127.0.0.1')
		self.localhostAfV4 = socket.AF_INET

		self.testByteRecv: List[int] = []

		# setup the mock TCP server
		self.mockServerAddr = self.localhostAddrV6
		self.mockServer = CreateMockTCPServer(
			self.mockServerAddr,
			self.testByteRecv,
		)
		self.mockServer.ThreadedServeUntilTerminate()
		self.mockServerPort = self.mockServer.server_address[1]

		# setup the test TCP server 1
		self.testServer1Addr = self.localhostAddrV6
		self.testServer1Af = self.localhostAfV6
		self.testServer1 = TCP.CreateServer(
			self.testServer1Addr,
			0,
			TCPwStaticIPConnector(self.mockServerAddr, self.mockServerPort),
		)
		self.testServer1Port = self.testServer1.server_address[1]
		self.testServer1.ThreadedServeUntilTerminate()

		# setup the test TCP server 2
		self.testServer2Addr = self.localhostAddrV4
		self.testServer2Af = self.localhostAfV4
		self.testServer2 = TCP.CreateServer(
			self.testServer2Addr,
			0,
			TCPwStaticIPConnector(self.mockServerAddr, self.mockServerPort),
		)
		self.testServer2Port = self.testServer2.server_address[1]
		self.testServer2.ThreadedServeUntilTerminate()

	def tearDown(self):
		# terminate Test server 1
		self.testServer1.Terminate()
		self.assertTrue(self.testServer1.terminateEvent.is_set())

		# terminate Test server 2
		self.testServer2.Terminate()
		self.assertTrue(self.testServer2.terminateEvent.is_set())

		# terminate Mock server
		self.mockServer.Terminate()
		self.assertTrue(self.mockServer.terminateEvent.is_set())

	def test_Inbound_TCP_01ServerReceive(self):
		logging.getLogger().info('')
		waitInterval = 0.1
		waitExpire = 5.0

		testData = b'Hello, World!'

		# test server 1
		with socket.socket(self.testServer1Af, socket.SOCK_STREAM) as s:
			s.connect((str(self.testServer1Addr), self.testServer1Port))
			s.sendall(testData)

		waitStart = time.time()
		while (
			(bytes(self.testByteRecv) != testData)
			and (time.time() - waitStart < waitExpire)
		):
			time.sleep(waitInterval)

		self.assertEqual(bytes(self.testByteRecv), testData)

		# clean up the test byte received
		self.testByteRecv.clear()
		self.assertEqual(bytes(self.testByteRecv), b'')

		# test server 2
		with socket.socket(self.testServer2Af, socket.SOCK_STREAM) as s:
			s.connect((str(self.testServer2Addr), self.testServer2Port))
			s.sendall(testData)

		waitStart = time.time()
		while (
			(bytes(self.testByteRecv) != testData)
			and (time.time() - waitStart < waitExpire)
		):
			time.sleep(waitInterval)

		self.assertEqual(bytes(self.testByteRecv), testData)

