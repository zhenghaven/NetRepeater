#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# Copyright (c) 2024 Haofan Zheng
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
###


from typing import Callable, Dict, Type

from .Handler import HandlerConnector
from .TCP import TCPwDynamicIPConnector, TCPwStaticIPConnector


CONNECTOR_MAP_TYPE = Dict[
	str,
	Type[HandlerConnector]
]


CONNECTOR_PROTO_MAP : Dict[str, CONNECTOR_MAP_TYPE] = {
	'tcp': {
		'dynamic': TCPwDynamicIPConnector,
		'static' : TCPwStaticIPConnector,
	},
}


def FindConnector(proto: str) -> CONNECTOR_MAP_TYPE:
	return CONNECTOR_PROTO_MAP.get(proto)

