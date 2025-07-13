#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# Copyright (c) 2024 Haofan Zheng
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
###


from typing import Callable, Dict

from ..Outbound.Handler import HandlerConnector
from .LegacyServer import Server
from .TCP import TCP
from .Utils import _IP_ADDRESS_TYPES


SERVER_CREATOR = Callable[
	[
		_IP_ADDRESS_TYPES,
		int,
		HandlerConnector
	],
	Server
]


SERVER_CREATOR_MAP : Dict[str, SERVER_CREATOR] = {
	'tcp': TCP.CreateServer,
}


def FindServerCreator(proto: str) -> SERVER_CREATOR:
	return SERVER_CREATOR_MAP.get(proto)

