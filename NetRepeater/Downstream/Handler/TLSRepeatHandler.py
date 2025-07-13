#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# Copyright (c) 2025 Haofan Zheng
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
###


import os
import socket

from PyNetworkLib.TLS.SSLContext import SSLContext

from .HandlerDict import HandlerDict
from .TCPRepeatHandler import TCPRepeatHandler


class TLSRepeatHandler(TCPRepeatHandler):

	@classmethod
	def FromConfig(
		cls,
		handlersDict: HandlerDict,
		*,
		ip: str,
		port: int,
		serverHostName: str,
		pollInterval: float = 0.1,
		readSize: int = 4096,
		caPEM: str | None = None,
		privKeyPath: os.PathLike | None = None,
		certPath: os.PathLike | None = None,
	) -> 'TLSRepeatHandler':
		return cls(
			ip=ip,
			port=port,
			serverHostName=serverHostName,
			pollInterval=pollInterval,
			readSize=readSize,
			caPEMorDER=caPEM,
			privKeyPath=privKeyPath,
			certPath=certPath,
		)

	def __init__(
		self,
		ip: str,
		port: int,
		serverHostName: str,
		pollInterval: float = 0.1,
		readSize: int = 4096,
		caPEMorDER: str | bytes | None = None,
		privKeyPath: os.PathLike | None = None,
		certPath: os.PathLike | None = None,
	) -> None:
		super().__init__(
			ip=ip,
			port=port,
			pollInterval=pollInterval,
			readSize=readSize,
		)

		self._serverHostName = serverHostName

		if privKeyPath is None or certPath is None:
			self._cltVerify = False
		else:
			self._cltVerify = True

		self._sslContext = SSLContext.CreateDefaultContext(
			isServerSide=False,
			caPEMorDER=caPEMorDER,
			isVerifyRequired=self._cltVerify,
		)

		if self._cltVerify:
			self._sslContext.LoadCertChainFiles(
				privKeyPath=privKeyPath,
				certChainPath=certPath,
			)

	def _DownstreamConnect(self) -> socket.socket:
		tcpSocket = super()._DownstreamConnect()
		try:
			return self._sslContext.WrapSocket(
				tcpSocket,
				server_side=False,
				server_hostname=self._serverHostName,
			)
		except Exception as e:
			tcpSocket.close()
			raise e

