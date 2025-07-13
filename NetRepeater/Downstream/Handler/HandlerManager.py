#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# Copyright (c) 2025 Haofan Zheng
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
###


import logging

from .HandlerDict import HandlerDict, HandlerModDict

from .AutoBlockByRate import AutoBlockByRate
from .TCPRepeatHandler import TCPRepeatHandler
from .TLSRepeatHandler import TLSRepeatHandler


HANDLER_MOD_DICT = HandlerModDict()
HANDLER_MOD_DICT.AddHandler('auto_block_by_rate', AutoBlockByRate)
HANDLER_MOD_DICT.AddHandler('tcp_repeat', TCPRepeatHandler)
HANDLER_MOD_DICT.AddHandler('tls_repeat', TLSRepeatHandler)


def BuildHandlerDictFromConfig(config: list[dict]) -> HandlerDict:
	'''
	Build a HandlerDict from a configuration list.

	:param config: A list of dictionaries, each containing handler configuration.
	:return: A HandlerDict containing the configured handlers.
	'''
	global HANDLER_MOD_DICT

	logger = logging.getLogger(f'{__name__}.BuildHandlerDictFromConfig')
	outHandlerDict = HandlerDict()

	for handlerConf in config:
		handlerName = handlerConf['name']
		handlerModule = handlerConf['module']
		handlerObjConf = handlerConf['config']

		logger.debug(f'Building handler {handlerName} with module {handlerModule}')

		handlerCls = HANDLER_MOD_DICT.GetHandler(handlerModule)

		handlerObj = handlerCls.FromConfig(
			handlersDict=outHandlerDict,
			**handlerObjConf
		)

		outHandlerDict.AddHandler(handlerName, handlerObj)

	return outHandlerDict

