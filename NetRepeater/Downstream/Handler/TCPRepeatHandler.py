#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# Copyright (c) 2025 Haofan Zheng
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
###


import ipaddress
import socket

from .HandlerDict import HandlerBase, HandlerDict
from .StreamRepeatHandlerBase import StreamRepeatHandlerBase


class TCPRepeatHandler(StreamRepeatHandlerBase, HandlerBase):
	'''
	A TCP/IP connector class that provides a method to create a connected
	downstream socket for TCP/IP connections.
	'''

	@classmethod
	def FromConfig(
		cls,
		handlersDict: HandlerDict,
		*,
		ip: str,
		port: int,
		pollInterval: float = 0.1,
		readSize: int = 4096,
	) -> 'TCPRepeatHandler':
		return cls(
			ip=ip,
			port=port,
			pollInterval=pollInterval,
			readSize=readSize,
		)

	def __init__(
		self,
		ip: str,
		port: int,
		pollInterval: float = 0.1,
		readSize: int = 4096,
	) -> None:
		self._ip = ipaddress.ip_address(ip)
		self._port = port

		if self._ip.version == 4:
			self._family = socket.AF_INET
		elif self._ip.version == 6:
			self._family = socket.AF_INET6
		else:
			raise ValueError(f'Unsupported IP version: {self._ip.version}')

		super().__init__(pollInterval=pollInterval, readSize=readSize)

	def _DownstreamConnect(self) -> socket.socket:
		'''
		Create a connected downstream socket for TCP/IP connections.

		:return: A connected socket instance.
		:rtype: socket.socket
		'''
		sock = socket.socket(self._family, socket.SOCK_STREAM)
		try:
			sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
			sock.connect((str(self._ip), self._port))
			return sock
		except Exception as e:
			sock.close()
			raise

