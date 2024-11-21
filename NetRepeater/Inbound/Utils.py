#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# Copyright (c) 2024 Haofan Zheng
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
###


import ipaddress
import socketserver

from typing import Type, Union

from ..Outbound import Handler
from .Server import Server as _Server


_IP_ADDRESS_TYPES = Union[ ipaddress.IPv4Address, ipaddress.IPv6Address ]


def CreateServer(
	address: _IP_ADDRESS_TYPES,
	port: int,
	handlerConnector: Handler.HandlerConnector,
	handlerType: Type[socketserver.BaseRequestHandler],
	serverV4Type: Type[_Server],
	serverV6Type: Type[_Server],
	handlerPollInterval: float = 0.5,
) -> _Server:

	serverTypeMap = {
		4: serverV4Type,
		6: serverV6Type,
	}
	serverType = serverTypeMap[address.version]

	serverInst = serverType((str(address), port), handlerType)
	serverInst.ServerInit({
		'handlerPollInterval': handlerPollInterval,
		'handlerConnector': handlerConnector,
	})

	return serverInst

