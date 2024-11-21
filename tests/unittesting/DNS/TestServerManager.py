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

import dns.rdata
import dns.rdataclass
import dns.rdatatype

from ModularDNS import Exceptions as _ModDNSExceptions
from ModularDNS.Downstream.Local.Hosts import Hosts

from NetRepeater.DNS.ServerManager import ServerItem, ServerManager

from ..MockServer import CreateMockTCPServer


class TestServerManager(unittest.TestCase):

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
		self.hosts.AddCNameRecord('localhostCNameV6', 'localhostV6.')
		self.hosts.AddRecord(
			domain='noAddrRec',
			rdCls=dns.rdataclass.IN,
			rdType=dns.rdatatype.TXT,
			rdata=dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.TXT, 'NoAddrRec')
		)

		# setup the mock TCP server 1
		self.mockServer1Addr = self.localhostAddrV6
		self.mockServer1 = CreateMockTCPServer(
			self.mockServer1Addr,
			self.testByteRecv,
		)
		self.mockServer1.ThreadedServeUntilTerminate()
		self.mockServer1Port = self.mockServer1.server_address[1]

	def tearDown(self):
		# terminate Mock server 1
		self.mockServer1.Terminate()
		self.assertTrue(self.mockServer1.terminateEvent.is_set())

	def test_DNS_ServerManager_01ServerItem(self):
		logging.getLogger().info('')
		waitInterval = 0.1
		waitExpire = 5.0

		testData = b'Hello, World!'

		# setup the test TCP server 1
		server1 = ServerItem(
			localIpAndNet=ipaddress.ip_interface('::1/128'),
			localIface='test_lo',
			localIfaceMode='linux-dry-run',
			protoAndPorts=[ ('tcp', 0, self.mockServer1Port ) ],
			remoteHost='localhostV6',
			remoteIPLookup=self.hosts,
		)

		try:
			self.assertEqual(len(self.testByteRecv), 0)
			with socket.socket(self.localhostAfV6, socket.SOCK_STREAM) as s:
				s.connect((
					str(server1._services[0].GetServerIP()),
					server1._services[0].GetServerPort()
				))
				s.sendall(testData)

			waitStart = time.time()
			while (
				(bytes(self.testByteRecv) != testData)
				and (time.time() - waitStart < waitExpire)
			):
				time.sleep(waitInterval)

			self.assertEqual(bytes(self.testByteRecv), testData)
			# cleanup the received data
			self.testByteRecv.clear()
			self.assertEqual(len(self.testByteRecv), 0)
		finally:
			server1.Terminate()

	def test_DNS_ServerManager_02ServerManager(self):
		logging.getLogger().info('')
		waitInterval = 0.1
		waitExpire = 5.0

		testData = b'Hello, World!'

		# setup server manager
		serverMgr = ServerManager(
			localNet=ipaddress.ip_network('::1/128'),
			localIface='test_lo',
			localIfaceMode='linux-dry-run',
			protoAndPorts=[ ('tcp', 0, self.mockServer1Port) ],
			remoteIPLookup=self.hosts,
			serverTTL=(10, 's'),
		)

		try:
			with serverMgr._cacheLock:
				serverItem1 = serverMgr._LookupOrCreateServerLockHeld('localhostV6')

			# send data
			self.assertEqual(len(self.testByteRecv), 0)
			with socket.socket(self.localhostAfV6, socket.SOCK_STREAM) as s:
				s.connect((
					str(serverItem1._services[0].GetServerIP()),
					serverItem1._services[0].GetServerPort()
				))
				s.sendall(testData)

			# wait for data to be received
			waitStart = time.time()
			while (
				(bytes(self.testByteRecv) != testData)
				and (time.time() - waitStart < waitExpire)
			):
				time.sleep(waitInterval)

			# check the received data
			self.assertEqual(bytes(self.testByteRecv), testData)
			# cleanup the received data
			self.testByteRecv.clear()
			self.assertEqual(len(self.testByteRecv), 0)

			# lookup the server again
			with serverMgr._cacheLock:
				serverItem2 = serverMgr._LookupOrCreateServerLockHeld('localhostV6')

			# check if the server is the same
			self.assertEqual(serverItem1, serverItem2)
		finally:
			serverMgr.Terminate()

	def test_DNS_ServerManager_02ServerManagerCName(self):
		logging.getLogger().info('')
		waitInterval = 0.1
		waitExpire = 5.0

		testData = b'Hello, World!'

		# setup server manager
		serverMgr = ServerManager(
			localNet=ipaddress.ip_network('::1/128'),
			localIface='test_lo',
			localIfaceMode='linux-dry-run',
			protoAndPorts=[ ('tcp', 0, self.mockServer1Port) ],
			remoteIPLookup=self.hosts,
			serverTTL=(10, 's'),
		)

		try:
			with serverMgr._cacheLock:
				serverItem1 = serverMgr._LookupOrCreateServerLockHeld('localhostCNameV6')

			# send data
			self.assertEqual(len(self.testByteRecv), 0)
			with socket.socket(self.localhostAfV6, socket.SOCK_STREAM) as s:
				s.connect((
					str(serverItem1._services[0].GetServerIP()),
					serverItem1._services[0].GetServerPort()
				))
				s.sendall(testData)

			# wait for data to be received
			waitStart = time.time()
			while (
				(bytes(self.testByteRecv) != testData)
				and (time.time() - waitStart < waitExpire)
			):
				time.sleep(waitInterval)

			# check the received data
			self.assertEqual(bytes(self.testByteRecv), testData)
			# cleanup the received data
			self.testByteRecv.clear()
			self.assertEqual(len(self.testByteRecv), 0)
		finally:
			serverMgr.Terminate()

	def test_DNS_ServerManager_03ServerManagerInvalidDomain(self):
		logging.getLogger().info('')
		waitInterval = 0.1
		waitExpire = 5.0

		testData = b'Hello, World!'

		# setup server manager
		serverMgr = ServerManager(
			localNet=ipaddress.ip_network('::1/128'),
			localIface='test_lo',
			localIfaceMode='linux-dry-run',
			protoAndPorts=[ ('tcp', 0, self.mockServer1Port) ],
			remoteIPLookup=self.hosts,
			serverTTL=(10, 's'),
		)

		try:
			with self.assertRaises(_ModDNSExceptions.DNSNameNotFoundError):
				serverMgr.LookupOrCreateServer('invalidDomain')

			with self.assertRaises(_ModDNSExceptions.DNSZeroAnswerError):
				serverMgr.LookupOrCreateServer('noAddrRec')
		finally:
			serverMgr.Terminate()

