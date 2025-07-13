#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# Copyright (c) 2025 Haofan Zheng
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
###


import os

from PyNetworkLib.Server.TLS.Server import ThreadingServer as _TLSServer
from PyNetworkLib.TLS.SSLContext import SSLContext

from ...Downstream.Handler.HandlerDict import HandlerDict as _DownstreamHandlerDict


class TLSServer(_TLSServer):

	@classmethod
	def FromConfig(
		cls,
		downstreamHandlerDict: _DownstreamHandlerDict,
		*,
		ip: str,
		port: int,
		downstream: str,
		privKeyPath: os.PathLike,
		certPath: os.PathLike,
		caPEMorDER: str | bytes | None = None,
		verifyClient: bool = False,
	) -> 'TLSServer':
		'''
		Create a TCP server from configuration.
		'''
		downstreamHandler = downstreamHandlerDict.GetHandler(downstream)

		sslContext = SSLContext.CreateDefaultContext(
			isServerSide=True,
			caPEMorDER=caPEMorDER,
			isVerifyRequired=verifyClient,
		)
		sslContext.LoadCertChainFiles(
			privKeyPath=privKeyPath,
			certChainPath=certPath,
		)

		return cls(
			server_address=(str(ip), int(port)),
			downstreamTCPHdlr=downstreamHandler,
			sslContext=sslContext,
		)

