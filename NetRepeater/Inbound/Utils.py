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
import socketserver
import threading
import uuid

from typing import Tuple, Type, Union

from ModularDNS.Server.Server import Server as _ModDNSServer

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

	serverUUID = uuid.uuid4()
	terminateEvent = threading.Event()

	handlerName = \
		f'{handlerType.__name__}_S[{address}]:{port}-{serverUUID.hex[:8]}'
	loggerName = f'{__name__}.{handlerName}'

	handlerLogger = logging.getLogger(loggerName)

	serverInst = serverType((str(address), port), handlerType)
	serverInst.ServerInit(serverUUID, terminateEvent)
	serverInst.ServerHandlerInit(
		handlerConnector=handlerConnector,
		handlerPollInterval=handlerPollInterval,
		handlerLogger=handlerLogger,
	)

	return serverInst


def FromModDNSServer(oriCls: Type[_ModDNSServer]) -> Type[_Server]:

	def ServerHandlerInit(
		self,
		handlerConnector    : Handler.HandlerConnector,
		handlerLogger       : logging.Logger,
		handlerPollInterval : float = 0.5,
	) -> None:
		self.handlerConnector    = handlerConnector
		self.handlerLogger       = handlerLogger
		self.handlerPollInterval = handlerPollInterval

	clsName = f'NetRepeater_{oriCls.__name__}'

	cls = type(
		clsName,
		(oriCls,),
		{
			'ServerHandlerInit': ServerHandlerInit,
		}
	)

	return cls

