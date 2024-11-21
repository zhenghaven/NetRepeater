#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# Copyright (c) 2024 Haofan Zheng
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
###


import selectors
import socket
import socketserver

from typing import Tuple

from  ModularDNS.Server.Server import FromPySocketServer

from ..Outbound import Handler
from .Server import Server as _Server
from .Utils import (
	_IP_ADDRESS_TYPES,
	CreateServer as _CreateServer,
	FromModDNSServer,
)


class TCPHandler(socketserver.StreamRequestHandler):
	disable_nagle_algorithm = True

	server: _Server

	def setup(self) -> None:
		super(TCPHandler, self).setup()

		self.pollInterval = self.server.handlerPollInterval
		self.outHandler = self.server.handlerConnector.Connect()
		self.readSize = 4096
		self.cltAddrStr = f'{self.client_address[0]}:{self.client_address[1]}'

	def handle(self):
		try:
			with selectors.DefaultSelector() as selector:
				selector.register(self.request, selectors.EVENT_READ)
				selector.register(self.outHandler, selectors.EVENT_READ)

				while not self.server.terminateEvent.is_set():
					for key, events in selector.select(self.pollInterval):
						if key.fileobj == self.request:
							# client sent some data
							# --> forward to server
							data = self.request.recv(self.readSize)
							if not data:
								# client closed the connection
								self.server.handlerLogger.debug(
									f'Client {self.cltAddrStr} closed the connection'
								)
								return
							self.outHandler.sendall(data)

						elif key.fileobj == self.outHandler:
							# server sent some data
							# --> forward to client
							data = self.outHandler.recv(self.readSize)
							if not data:
								# server closed the connection
								self.server.handlerLogger.debug(
									f'Server {self.outHandler.getpeername()} closed the connection'
								)
								return
							self.request.sendall(data)

						else:
							raise ValueError('Unknown file object')
		except Exception as e:
			self.server.handlerLogger.error(
				f'Handler for {self.cltAddrStr} failed with error: {e}'
			)

	def finish(self) -> None:
		self.outHandler.close()
		self.server.handlerLogger.debug(f'Finishing {self.cltAddrStr} handler')
		super(TCPHandler, self).finish()


@FromModDNSServer
@FromPySocketServer
class TCPServerV4(socketserver.ThreadingTCPServer):
	address_family = socket.AF_INET


@FromModDNSServer
@FromPySocketServer
class TCPServerV6(socketserver.ThreadingTCPServer):
	address_family = socket.AF_INET6


class TCP:

	@classmethod
	def CreateServer(
		cls,
		address: _IP_ADDRESS_TYPES,
		port: int,
		handlerConnector: Handler.HandlerConnector,
	) -> _Server:

		return _CreateServer(
			address=address,
			port=port,
			handlerConnector=handlerConnector,
			handlerType=TCPHandler,
			serverV4Type=TCPServerV4,
			serverV6Type=TCPServerV6,
		)

