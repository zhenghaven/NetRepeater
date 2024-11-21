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

from typing import Callable, Union

from .Handler import HandlerConnector, SocketHandler


_IP_ADDRESS_TYPES = Union[ ipaddress.IPv4Address, ipaddress.IPv6Address ]


class TCPwDynamicIPConnector(HandlerConnector):

	def __init__(
		self,
		hostName: str,
		port: int,
		addrLookup: Callable[[str], _IP_ADDRESS_TYPES],
	) -> None:
		super(TCPwDynamicIPConnector, self).__init__()

		self.hostName = hostName
		self.port = port
		self.addrLookup = addrLookup

		self.hostAddrStr = f'{self.hostName}:{self.port}'
		self.logger = logging.getLogger(
			f'{__name__}.{self.__class__.__name__}.{self.hostAddrStr}'
		)

	def Connect(self) -> SocketHandler:
		ipAddr = self.addrLookup(self.hostName)
		if ipAddr.version == 4:
			af = socket.AF_INET
		elif ipAddr.version == 6:
			af = socket.AF_INET6
		else:
			raise ValueError(f'Unknown IP address version: {ipAddr.version}')
		ipAddrStr = str(ipAddr)

		sock = socket.socket(af, socket.SOCK_STREAM)
		# set TCP_NODELAY to disable Nagle's algorithm
		sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
		sock.connect((ipAddrStr, self.port))

		return SocketHandler(sock, logger=self.logger)


class TCPwStaticIPConnector(TCPwDynamicIPConnector):

	def __init__(
		self,
		ipAddr: _IP_ADDRESS_TYPES,
		port: int,
	) -> None:
		super(TCPwStaticIPConnector, self).__init__(
			str(ipAddr),
			port,
			lambda _: ipAddr
		)

