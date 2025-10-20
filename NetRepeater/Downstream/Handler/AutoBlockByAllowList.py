#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# Copyright (c) 2025 Haofan Zheng
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
###


import os

from PyNetworkLib.Server.Utils.DownstreamAllowList import DownstreamAllowList

from .HandlerDict import HandlerDict, HandlerBase


class AutoBlockByAllowList(DownstreamAllowList, HandlerBase):
	'''
	AutoBlockByRate is a class that extends DownstreamHandlerBlockByRate.
	'''

	@classmethod
	def FromConfig(
		cls,
		handlersDict: HandlerDict,
		*,
		allowListOrFile: os.PathLike | list[str],
		downstreamHandler: str,
		logIPs: bool = False,
	) -> 'AutoBlockByAllowList':

		downstreamHandlerObj = handlersDict.GetHandler(downstreamHandler)

		return cls(
			allowListOrFile=allowListOrFile,
			downstreamHandler=downstreamHandlerObj,
			logIPs=logIPs,
		)

