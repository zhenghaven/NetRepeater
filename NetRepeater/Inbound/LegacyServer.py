#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# Copyright (c) 2024 Haofan Zheng
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
###


from ModularDNS.Server.Server import Server as _BaseServer

from ..Outbound import Handler


class Server(_BaseServer):

	handlerPollInterval : float
	handlerConnector    : Handler.HandlerConnector

