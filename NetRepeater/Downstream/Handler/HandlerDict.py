#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# Copyright (c) 2025 Haofan Zheng
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
###


import logging
import threading

from typing import Generic, Type, TypeVar

from PyNetworkLib.Server.TCP.DownstreamHandlerBase import DownstreamHandlerBase


class HandlerBase(DownstreamHandlerBase):
	'''
	HandlerBase is a base class for downstream handlers.
	It extends DownstreamHandlerBase and provides a common interface for downstream handlers.
	'''

	@classmethod
	def FromConfig(
		cls,
		handlersDict: 'HandlerDict',
		**kwargs,
	) -> 'HandlerBase':
		'''
		Create an instance of HandlerBase from a configuration dictionary.

		'''
		raise NotImplementedError(f'{cls.__name__}.FromConfig is not implemented.')


# type of items in the dictionary
_T = TypeVar('_T')


class HandlerDictBase(Generic[_T]):
	'''A dictionary to manage downstream handlers.'''

	def __init__(self):
		self._handlers = {}
		self._handlersLock = threading.Lock()
		self._logger = logging.getLogger(f'{__name__}.{self.__class__.__name__}')

	def AddHandler(self, name: str, handler: _T) -> None:
		'''Add a handler to the dictionary.'''
		with self._handlersLock:
			if name in self._handlers:
				raise KeyError(f'Handler with name {name} already exists.')
			self._handlers[name] = handler
			self._logger.debug(f'Handler {name} added.')

	def GetHandler(self, name: str) -> _T:
		'''Get a handler by name.'''
		with self._handlersLock:
			if name not in self._handlers:
				raise KeyError(f'Handler with name {name} does not exist.')
			return self._handlers[name]


	def __setitem__(self, name: str, handler: _T) -> None:
		'''Set a handler by name.'''
		return self.AddHandler(name, handler)

	def __getitem__(self, name: str) -> _T:
		'''Get a handler by name.'''
		return self.GetHandler(name)

	def __contains__(self, name: str) -> bool:
		'''Check if a handler exists by name.'''
		with self._handlersLock:
			return name in self._handlers


class HandlerDict(HandlerDictBase[HandlerBase]):
	pass


class HandlerModDict(HandlerDictBase[Type[HandlerBase]]):
	pass
