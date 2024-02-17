#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# Copyright (c) 2024 Haofan Zheng
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
###


import socketserver
import typing
import typing_extensions

from . import TCP


InboundServerCreator : typing_extensions.TypeAlias = typing.Callable[[typing.Any], socketserver.BaseServer]


INBOUND_SERVER_CREATOR_MAP : typing.Dict[str, InboundServerCreator] = {
	'tcp': TCP.CreateTCPServer
}


def FindInboundServerCreator(proto: str) -> InboundServerCreator:
	return INBOUND_SERVER_CREATOR_MAP.get(proto)

