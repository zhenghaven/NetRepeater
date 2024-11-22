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

import dns.message
import dns.name
import dns.rdata
import dns.rdataclass
import dns.rdatatype

from ModularDNS import Exceptions as _ModDNSExceptions
from ModularDNS.Downstream.DownstreamCollection import DownstreamCollection
from ModularDNS.Downstream.Local.Hosts import Hosts

from NetRepeater.DNS.NetRepeaterMod import ServerManagerMod

from ..MockServer import CreateMockTCPServer


class TestNetRepeaterMod(unittest.TestCase):

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

	def test_DNS_NetRepeaterMod_01FullSetupAndTest(self):
		logging.getLogger().info('')
		waitInterval = 0.1
		waitExpire = 5.0

		testData = b'Hello, World!'


		dCollection = DownstreamCollection()
		dCollection.AddHandler('hosts', self.hosts)


		# setup the DNS module
		mod = ServerManagerMod.FromConfig(
			dCollection=dCollection,
			localNet='::1/128',
			localIface='test_lo',
			localIfaceMode='linux-dry-run',
			protoAndPorts=[ ['tcp', 0, self.mockServer1Port] ],
			remoteIPLookup='s:hosts',
			serverTTL=[1, 'd'],
		)

		try:
			self.assertEqual(
				mod._serverManager._serverTTL,
				(1 * 24 * 3600, 's')
			)

			mod.LookupIpAddr(
				domain='localhostV6',
				recDepthStack=[],
			)

			server = mod._serverManager._cache.Get('localhostV6')

			self.assertEqual(len(self.testByteRecv), 0)
			with socket.socket(self.localhostAfV6, socket.SOCK_STREAM) as s:
				s.connect((
					str(server._services[0].GetServerIP()),
					server._services[0].GetServerPort()
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
			mod.Terminate()

	def test_DNS_NetRepeaterMod_02RespForIPv6Only(self):
		logging.getLogger().info('')

		dCollection = DownstreamCollection()
		dCollection.AddHandler('hosts', self.hosts)


		# setup the DNS module
		mod = ServerManagerMod.FromConfig(
			dCollection=dCollection,
			localNet='::1/128',
			localIface='test_lo',
			localIfaceMode='linux-dry-run',
			protoAndPorts=[ ['tcp', 0, self.mockServer1Port] ],
			remoteIPLookup='s:hosts',
			serverTTL=[1, 'd'],
		)

		try:
			query = dns.message.make_query(
				qname='localhostV6',
				rdtype=dns.rdatatype.A,
				rdclass=dns.rdataclass.IN,
			)

			resp = mod.Handle(
				query,
				senderAddr=('localhost', 0),
				recDepthStack=[],
			)

			self.assertEqual(len(resp.answer), 0)
			self.assertEqual(len(resp.additional), 1)
			self.assertEqual(resp.additional[0].name, dns.name.from_text('localhostV6'))
			self.assertEqual(resp.additional[0].rdclass, dns.rdataclass.IN)
			self.assertEqual(resp.additional[0].rdtype, dns.rdatatype.AAAA)
			items = [ x for x in resp.additional[0].items ]
			self.assertEqual(len(items), 1)
			self.assertEqual(
				ipaddress.ip_address(items[0].address),
				self.localhostAddrV6
			)
		finally:
			mod.Terminate()

