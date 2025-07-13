#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# Copyright (c) 2025 Haofan Zheng
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
###


import os

from PyNetworkLib.Server.Utils.DownstreamHandlerBlockByRate import DownstreamHandlerBlockByRate

from .HandlerDict import HandlerDict, HandlerBase


class AutoBlockByRate(DownstreamHandlerBlockByRate, HandlerBase):
	'''
	AutoBlockByRate is a class that extends DownstreamHandlerBlockByRate.
	'''

	@classmethod
	def FromConfig(
		cls,
		handlersDict: HandlerDict,
		*,
		maxNumRequests: int,
		timeWindowSec: float,
		downstreamHandler: str,
		savedStatePath: None | os.PathLike = None,
		globalStatePath: None | os.PathLike = None,
		logIPs: bool = False,
	) -> 'AutoBlockByRate':

		downstreamHandlerObj = handlersDict.GetHandler(downstreamHandler)

		return cls(
			maxNumRequests=maxNumRequests,
			timeWindowSec=timeWindowSec,
			downstreamHandler=downstreamHandlerObj,
			savedStatePath=savedStatePath,
			globalStatePath=globalStatePath,
			logIPs=logIPs,
		)

