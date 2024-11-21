#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# Copyright (c) 2024 Haofan Zheng
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
###


import ipaddress
import selectors
import socket
import socketserver
import threading
import uuid

from typing import List, Union

from ModularDNS.Server.Server import FromPySocketServer


_IP_ADDRESS_TYPES = Union[ipaddress.IPv4Address, ipaddress.IPv6Address]


@FromPySocketServer
class MockTCPServerV4(socketserver.ThreadingTCPServer):
	address_family = socket.AF_INET

	def ServerTestInit(self, testByteRecv: List[int]) -> None:
		self.testByteRecv = testByteRecv


@FromPySocketServer
class MockTCPServerV6(socketserver.ThreadingTCPServer):
	address_family = socket.AF_INET6

	def ServerTestInit(self, testByteRecv: List[int]) -> None:
		self.testByteRecv = testByteRecv


class MockTCPHandler(socketserver.StreamRequestHandler):
	disable_nagle_algorithm = True

	server: MockTCPServerV6

	def setup(self) -> None:
		super(MockTCPHandler, self).setup()

		self.pollInterval = 0.5
		self.readSize = 4096
		self.cltAddrStr = f'{self.client_address[0]}:{self.client_address[1]}'

	def handle(self):
		try:
			with selectors.DefaultSelector() as selector:
				selector.register(self.request, selectors.EVENT_READ)

				while not self.server.terminateEvent.is_set():
					for key, events in selector.select(self.pollInterval):
						if key.fileobj == self.request:
							# client sent some data
							# --> forward to server
							data = self.request.recv(self.readSize)
							if not data:
								# client closed the connection
								return
							for b in data:
								self.server.testByteRecv.append(b)

						else:
							raise ValueError('Unknown file object')
		except Exception as e:
			pass

	def finish(self) -> None:
		super(MockTCPHandler, self).finish()


def CreateMockTCPServer(
	address: _IP_ADDRESS_TYPES,
	testByteRecv: List[int],
) -> MockTCPServerV6:
	mockServerUUID = uuid.uuid4()
	mockServerTerminateEvent = threading.Event()

	if address.version == 4:
		serverCls = MockTCPServerV4
	elif address.version == 6:
		serverCls = MockTCPServerV6
	else:
		raise ValueError(f'Unknown IP address version: {address.version}')

	mockServer = serverCls(
		(str(address), 0),
		MockTCPHandler,
	)
	mockServer.ServerInit(mockServerUUID, mockServerTerminateEvent)
	mockServer.ServerTestInit(testByteRecv)

	return mockServer

