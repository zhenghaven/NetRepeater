#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# Copyright (c) 2024 Haofan Zheng
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
###


import logging
import socket

from typing_extensions import TypeAlias


ReadableBuffer: TypeAlias = bytes


class Handler(object):

	def __init__(self) -> None:
		super(Handler, self).__init__()

	def sendall(self, data: ReadableBuffer) -> None:
		raise NotImplementedError('Send() is not implemented')

	def fileno(self) -> int:
		# interface required by select.select()
		raise NotImplementedError('fileno() is not implemented')

	def recv(self, bufsize: int) -> bytes:
		raise NotImplementedError('recv() is not implemented')

	def getpeername(self) -> str:
		raise NotImplementedError('getpeername() is not implemented')

	def close(self) -> None:
		raise NotImplementedError('close() is not implemented')


class SocketHandler(Handler):

	def __init__(self, sock: socket.socket, logger: logging.Logger) -> None:
		super(SocketHandler, self).__init__()

		self.logger = logger
		self.sock = sock
		self.peername = self.sock.getpeername()

	def sendall(self, data: ReadableBuffer) -> None:
		self.sock.sendall(data)

	def fileno(self) -> int:
		return self.sock.fileno()

	def recv(self, bufsize: int) -> bytes:
		return self.sock.recv(bufsize)

	def getpeername(self) -> str:
		return self.peername

	def close(self) -> None:
		self.sock.close()
		self.logger.debug(f'{self.getpeername()} Socket closed')


class HandlerConnector(object):

	def __init__(self) -> None:
		super(HandlerConnector, self).__init__()

	def Connect(self) -> Handler:
		raise NotImplementedError('Connect() is not implemented')

