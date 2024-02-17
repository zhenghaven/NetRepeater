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
import selectors
import socket
import socketserver
import threading

from ..Outbound import Handler


class TCPHandler(socketserver.StreamRequestHandler):
	disable_nagle_algorithm = True

	def GetOutboundConnector(self) -> Handler.HandlerConnector:
		raise NotImplementedError('GetOutboundConnector() is not implemented')

	def GetOutboundHandler(self) -> Handler.Handler:
		return self.GetOutboundConnector().Connect()

	def GetPollInterval(self) -> float:
		raise NotImplementedError('GetPollInterval() is not implemented')

	def IsServerTerminated(self) -> bool:
		raise NotImplementedError('IsServerTerminated() is not implemented')

	def setup(self) -> None:
		super(TCPHandler, self).setup()

		self.pollInterval = self.GetPollInterval()
		self.outHandler = self.GetOutboundHandler()
		self.readSize = 4096
		self.cltAddrStr = f'{self.client_address[0]}:{self.client_address[1]}'

	def handle(self):
		try:
			with selectors.DefaultSelector() as selector:
				selector.register(self.request, selectors.EVENT_READ)
				selector.register(self.outHandler, selectors.EVENT_READ)

				while not self.IsServerTerminated():
					for key, events in selector.select(self.pollInterval):
						if key.fileobj == self.request:
							# client sent some data
							# --> forward to server
							data = self.request.recv(self.readSize)
							if not data:
								# client closed the connection
								self.server.logger.debug(
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
								self.server.logger.debug(
									f'Server {self.outHandler.getpeername()} closed the connection'
								)
								return
							self.request.sendall(data)

						else:
							raise ValueError('Unknown file object')
		except Exception as e:
			self.server.logger.error(
				f'Handler for {self.cltAddrStr} failed with error: {e}'
			)

	def finish(self) -> None:
		self.outHandler.close()
		self.server.logger.debug(f'Finishing {self.cltAddrStr} handler')
		super(TCPHandler, self).finish()


def _GetAddrFamByHost(host: str) -> int:
	ipAddr = ipaddress.ip_address(host)
	if ipAddr.version == 4:
		return socket.AF_INET
	elif ipAddr.version == 6:
		return socket.AF_INET6
	else:
		raise ValueError('Unsupported IP version')


def CreateTCPServer(
	host: str,
	port: int,
	outboundConnector: Handler.HandlerConnector,
	pollInterval: float = 0.5
) -> socketserver.ThreadingTCPServer:
	terminatingSignal = threading.Event()

	class TerminatableTCPHandler(TCPHandler):
		IS_SERVER_TERMINATED = terminatingSignal
		OUTBOUND_CONNECTOR = outboundConnector
		POLL_INTERVAL = pollInterval

		def GetOutboundConnector(self) -> Handler.HandlerConnector:
			return self.OUTBOUND_CONNECTOR

		def GetPollInterval(self) -> float:
			return self.POLL_INTERVAL

		def IsServerTerminated(self) -> bool:
			return self.IS_SERVER_TERMINATED.is_set()

	class TCPServer(socketserver.ThreadingTCPServer):
		address_family = _GetAddrFamByHost(host)

		IS_SERVER_TERMINATED = terminatingSignal

		def __init__(
			self,
			server_address,
			RequestHandlerClass,
			bind_and_activate=True
		):
			self.svrAddrStr = f'{server_address[0]}:{server_address[1]}'
			self.logger = logging.getLogger(
				f'{__name__}.{self.__class__.__name__}.{self.svrAddrStr}'
			)

			super(TCPServer, self).__init__(
				server_address=server_address,
				RequestHandlerClass=RequestHandlerClass,
				bind_and_activate=bind_and_activate
			)

		def serve_forever(self, poll_interval=pollInterval):
			super(TCPServer, self).serve_forever(poll_interval=poll_interval)

		def shutdown(self) -> None:
			self.IS_SERVER_TERMINATED.set()
			super(TCPServer, self).shutdown()

	return TCPServer((host, port), TerminatableTCPHandler)

