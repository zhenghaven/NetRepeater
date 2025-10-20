#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# Copyright (c) 2025 Haofan Zheng
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
###


import os

from PyNetworkLib.Server.HTTPS.Server import ThreadingServer as _HTTPSServer
from PyNetworkLib.TLS.SSLContext import SSLContext

from ...Downstream.Handler.HandlerDict import HandlerDict as _DownstreamHandlerDict


class HTTPSServer(_HTTPSServer):

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
	) -> 'HTTPSServer':
		'''
		Create a HTTPS server from configuration.
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
			downstreamHTTPHdlr=downstreamHandler,
			sslContext=sslContext,
			enabledCommands=['GET', 'POST', 'PUT', 'DELETE', 'HEAD', 'OPTIONS', 'PATCH', 'TRACE', 'CONNECT'],
		)

