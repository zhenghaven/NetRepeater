#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# Copyright (c) 2025 Haofan Zheng
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
###


import selectors
import socket
import threading

from PyNetworkLib.Server.TCP.DownstreamHandlerBase import DownstreamHandlerBase
from PyNetworkLib.Server.TCP.PyHandlerBase import PyHandlerBase
from PyNetworkLib.Server.Utils.HandlerState import HandlerState


class StreamRepeatHandlerBase(DownstreamHandlerBase):
	'''
	A simple TCP handler that repeats data between the upstream and downstream
	connections made by the handler connector.
	'''

	def __init__(
		self,
		pollInterval: float = 0.1,
		readSize: int = 4096,
	) -> None:
		super().__init__()

		self._pollInterval = pollInterval
		self._readSize = readSize

	def _DownstreamConnect(self) -> socket.socket:
		'''
		This method should be overridden by subclasses to establish a connection
		to the downstream server.
		'''
		raise NotImplementedError('This method should be overridden by subclasses.')

	def HandleRequest(
		self,
		*,
		pyHandler: PyHandlerBase,
		handlerState : HandlerState,
		reqState: dict,
		terminateEvent: threading.Event,
	) -> None:
		with self._DownstreamConnect() as downstreamHandler:
			try:
				with selectors.DefaultSelector() as selector:
					selector.register(pyHandler.request, selectors.EVENT_READ)
					selector.register(downstreamHandler, selectors.EVENT_READ)

					while not terminateEvent.is_set():
						for key, events in selector.select(self._pollInterval):
							if key.fileobj == pyHandler.request:
								# client sent some data
								# --> forward to server
								data = pyHandler.request.recv(self._readSize)
								if not data:
									# client closed the connection
									pyHandler.server.handlerLogger.debug(
										f'Upstream {pyHandler.client_address} closed the connection'
									)
									return
								downstreamHandler.sendall(data)

							elif key.fileobj == downstreamHandler:
								# server sent some data
								# --> forward to client
								data = downstreamHandler.recv(self._readSize)
								if not data:
									# server closed the connection
									pyHandler.server.handlerLogger.debug(
										f'Downstream {downstreamHandler.getpeername()} closed the connection'
									)
									return
								pyHandler.request.sendall(data)

							else:
								raise ValueError('Unknown file object')
			except Exception as e:
				self.server.handlerLogger.debug(
					f'Handler for {pyHandler.client_address} failed with error: {e}'
				)
				pass

