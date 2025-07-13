#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# Copyright (c) 2025 Haofan Zheng
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
###


from PyNetworkLib.Server.ServerBase import ServerBase as _ServerBase

from ...Downstream.Handler.HandlerDict import HandlerDict as _DownstreamHandlerDict
from .TCP import TCPServer
from .TLS import TLSServer


_MOD_DICT = {
	'TCP': TCPServer,
	'TLS': TLSServer,
}


def CreateServerFromConfig(
	config: list[dict],
	downstreamHandlerDict: _DownstreamHandlerDict,
) -> list[_ServerBase]:

	outServers = []

	for serverConf in config:
		serverMod = serverConf['module']
		serverObjConf = serverConf['config']

		serverCls = _MOD_DICT[serverMod]

		serverObj = serverCls.FromConfig(
			downstreamHandlerDict=downstreamHandlerDict,
			**serverObjConf,
		)

		outServers.append(serverObj)

	return outServers

