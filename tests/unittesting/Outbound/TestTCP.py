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

from ModularDNS.Downstream.Local.Hosts import Hosts

from NetRepeater.Inbound.TCP import TCP
from NetRepeater.Outbound.TCP import TCPwDynamicIPConnector

from ..MockServer import CreateMockTCPServer


class TestTCPHandler(unittest.TestCase):

	def setUp(self):
		self.localhostAddrV6 = ipaddress.ip_address('::1')
		self.localhostAfV6 = socket.AF_INET6
		self.localhostAddrV4 = ipaddress.ip_address('127.0.0.1')
		self.localhostAfV4 = socket.AF_INET

		self.testByteRecv: List[int] = []

		# setup hosts DNS lookup
		self.hosts = Hosts()
		self.hosts.AddAddrRecord('localhostV6', self.localhostAddrV6)
		self.hosts.AddAddrRecord('localhostV4', self.localhostAddrV4)
		def addrLookup(hostName: str):
			return self.hosts.LookupIpAddr(hostName, [])

		# setup the mock TCP server 1
		self.mockServer1Addr = self.localhostAddrV6
		self.mockServer1 = CreateMockTCPServer(
			self.mockServer1Addr,
			self.testByteRecv,
		)
		self.mockServer1.ThreadedServeUntilTerminate()
		self.mockServer1Port = self.mockServer1.server_address[1]

		# setup the mock TCP server 2
		self.mockServer2Addr = self.localhostAddrV4
		self.mockServer2 = CreateMockTCPServer(
			self.mockServer2Addr,
			self.testByteRecv,
		)
		self.mockServer2.ThreadedServeUntilTerminate()
		self.mockServer2Port = self.mockServer2.server_address[1]

		# setup the test TCP server 1
		self.testServer1Addr = self.localhostAddrV6
		self.testServer1Af = self.localhostAfV6
		self.testServer1 = TCP.CreateServer(
			self.testServer1Addr,
			0,
			TCPwDynamicIPConnector('localhostV6', self.mockServer1Port, addrLookup),
		)
		self.testServer1.ThreadedServeUntilTerminate()
		self.testServer1Port = self.testServer1.server_address[1]

		# setup the test TCP server 2
		self.testServer2Addr = self.localhostAddrV4
		self.testServer2Af = self.localhostAfV4
		self.testServer2 = TCP.CreateServer(
			self.testServer2Addr,
			0,
			TCPwDynamicIPConnector('localhostV4', self.mockServer2Port, addrLookup),
		)
		self.testServer2.ThreadedServeUntilTerminate()
		self.testServer2Port = self.testServer2.server_address[1]

	def tearDown(self):
		# terminate Test server 1
		self.testServer1.Terminate()
		self.assertTrue(self.testServer1.terminateEvent.is_set())

		# terminate Test server 2
		self.testServer2.Terminate()
		self.assertTrue(self.testServer2.terminateEvent.is_set())

		# terminate Mock server 1
		self.mockServer1.Terminate()
		self.assertTrue(self.mockServer1.terminateEvent.is_set())

		# terminate Mock server 2
		self.mockServer2.Terminate()
		self.assertTrue(self.mockServer2.terminateEvent.is_set())

	def test_Outbound_TCP_01HandlerSend(self):
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

