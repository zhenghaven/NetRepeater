#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# Copyright (c) 2025 Haofan Zheng
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
###


from PyNetworkLib.Server.TCP.Server import ThreadingServer as _TCPServer

from ...Downstream.Handler.HandlerDict import HandlerDict as _DownstreamHandlerDict


class TCPServer(_TCPServer):

	@classmethod
	def FromConfig(
		cls,
		downstreamHandlerDict: _DownstreamHandlerDict,
		*,
		ip: str,
		port: int,
		downstream: str,
	) -> 'TCPServer':
		'''
		Create a TCP server from configuration.
		'''
		downstreamHandler = downstreamHandlerDict.GetHandler(downstream)

		return cls(
			server_address=(str(ip), int(port)),
			downstreamTCPHdlr=downstreamHandler,
		)

