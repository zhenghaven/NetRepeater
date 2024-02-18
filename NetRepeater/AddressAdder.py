#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# Copyright (c) 2024 Haofan Zheng
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
###


import ipaddress
import logging
import subprocess
import sys
import time

from typing import List


class AddressAdder(object):

	@classmethod
	def _RunSysCmd(cls, cmd: list) -> None:
		proc = subprocess.Popen(cmd, stdout=sys.stdout, stderr=sys.stderr)
		proc.wait()

		if proc.returncode != 0:
			cmdStr = ' '.join(cmd)
			raise RuntimeError(f'Command "{cmdStr}" failed with return code {proc.returncode}')

		time.sleep(2) # Wait for the settings to take effect

	def __init__(self, dev: str) -> None:
		super(AddressAdder, self).__init__()

		self.dev = dev
		self.logger = logging.getLogger(f'{__name__}.{self.__class__.__name__}.{self.dev}')

	def AddAddress(self, address: str, prefix: int) -> None:
		ipaddr = ipaddress.ip_address(address)

		# Add the address to the device
		ipaddrWithPrefix = f'{ipaddr}/{prefix}'
		self.logger.info(f'Adding address {ipaddrWithPrefix} to {self.dev}')

		if sys.platform == 'linux':
			cmd = [ 'ip', 'addr', 'add', ipaddrWithPrefix, 'dev', self.dev ]
			self._RunSysCmd(cmd)
		else:
			raise NotImplementedError(f'Platform {sys.platform} not supported')

	def AddAddresses(self, addresses: List[dict]) -> None:
		for addr in addresses:
			self.AddAddress(addr['address'], addr['prefix'])

