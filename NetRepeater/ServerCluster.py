#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# Copyright (c) 2024 Haofan Zheng
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
###


import logging
import signal
import socketserver
import threading

from typing import List


class ServerCluster(object):

	@classmethod
	def OneServerThread(cls, svr: socketserver.BaseServer) -> None:
		svr.serve_forever()

	def __init__(self) -> None:
		super(ServerCluster, self).__init__()

		self.logger = logging.getLogger(f'{__name__}.{self.__class__.__name__}')

		self.manageLock = threading.Lock()
		self.isStarted = threading.Event()
		self.isTerminate = threading.Event()
		self.servers: List[socketserver.BaseServer] = []

	def AddServer(self, server: socketserver.BaseServer) -> None:
		self.servers.append(server)

	def Start(self) -> None:
		with self.manageLock:
			if self.isStarted.is_set():
				return

			self.logger.info('Starting server cluster')
			self.isStarted.set()
			for svr in self.servers:
				thread = threading.Thread(target=self.OneServerThread, args=(svr,))
				thread.start()

	def Stop(self) -> None:
		with self.manageLock:
			if not self.isStarted.is_set():
				return

			self.logger.info('Stopping server cluster')
			self.isStarted.clear()
			for svr in self.servers:
				svr.shutdown()
				svr.server_close()
			self.isTerminate.set()

	def StopBySignal(self, signum, frame) -> None:
		self.Stop()

	def ServeUntilSignals(
		self,
		signals: List[signal.Signals] = [signal.SIGINT, signal.SIGTERM]
	) -> None:
		self.Start()

		for sig in signals:
			signal.signal(sig, self.StopBySignal)

		self.isTerminate.wait()

		for sig in signals:
			signal.signal(sig, signal.SIG_DFL)

