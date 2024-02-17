#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# Copyright (c) 2024 Haofan Zheng
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
###


import typing

from . import TCP, Handler


OUTBOUND_CONNECTOR_MAP : typing.Dict[str, Handler.HandlerConnector] = {
	'tcp': TCP.TCPConnector
}


def FindOutboundConnector(proto: str) -> Handler.HandlerConnector:
	return OUTBOUND_CONNECTOR_MAP.get(proto)

