#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# Copyright (c) 2024 Haofan Zheng
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
###


import logging
import socket

from .Handler import HandlerConnector, SocketHandler


class TCPConnector(HandlerConnector):

	def __init__(
		self,
		host: str,
		port: int,
		*args, **kwargs
	) -> None:
		super(TCPConnector, self).__init__()

		self.host = host
		self.port = port
		self.hostAddrStr = f'{host}:{port}'
		self.logger = logging.getLogger(
			f'{__name__}.{self.__class__.__name__}.{self.hostAddrStr}'
		)

	def Connect(self) -> SocketHandler:
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		# set TCP_NODELAY to disable Nagle's algorithm
		sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
		sock.connect((self.host, self.port))

		return SocketHandler(sock, logger=self.logger)

