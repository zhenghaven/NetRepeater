#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# Copyright (c) 2024 Haofan Zheng
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
###


import hashlib
import ipaddress
import logging

from typing import Callable, List, Union


_IP_ADDRESS_TYPES = Union[ ipaddress.IPv4Address, ipaddress.IPv6Address ]
_IP_NETWORK_TYPES = Union[ ipaddress.IPv4Network, ipaddress.IPv6Network ]


class SiteUIDGenerator(object):

	def __init__(self, siteName: str) -> None:
		super(SiteUIDGenerator, self).__init__()

		self.siteName = siteName

		self.m = hashlib.sha256()
		self.m.update(self.siteName.encode('utf-8'))
		self.uidBytes = self.m.digest()

	def GetUIDBytes(self) -> bytes:
		return self.uidBytes

	def GetUIDInt(self) -> int:
		return int.from_bytes(self.uidBytes, byteorder='big')

	def NextIteration(self, n: int = 1) -> None:
		for _ in range(n):
			self.m.update(self.uidBytes)
			self.uidBytes = self.m.digest()


class RandIPGenerator(object):

	def __init__(
		self,
		network: _IP_NETWORK_TYPES,
	) -> None:
		super(RandIPGenerator, self).__init__()

		self.network = network

		self.netAddrLenBits    = self.network.max_prefixlen
		# self.netAddrLenBytes   = self.netAddrLenBits // 8
		# self.netPrefixLenBytes = self.network.prefixlen // 8
		self.suffixLenBits	   = self.netAddrLenBits  - self.network.prefixlen
		# self.suffixLenBytes    = self.netAddrLenBytes - self.netPrefixLenBytes

		self.netInt = int(self.network.network_address) # & int(self.network.netmask)
		self.hostmaskInt = int(self.network.hostmask) # << self.network.prefixlen
		self.netCls = self.network.network_address.__class__

		self.logger = logging.getLogger(f'{__name__}.{self.__class__.__name__}')

	def _GenerateFromInt(self, num: int) -> _IP_ADDRESS_TYPES:
		numLenBits = num.bit_length()
		if numLenBits < self.suffixLenBits:
			raise ValueError(
				f'The given integer is too small to generate the suffix of IP'
				f' (Need={self.suffixLenBits} bits, received={numLenBits}) bits'
			)

		suffixInt = num & self.hostmaskInt
		hostInt = self.netInt | suffixInt

		hostIp = self.netCls(hostInt)

		# verify that we generate the address correctly
		if hostIp not in self.network:
			raise RuntimeError(f'Failed to generate the address')

		return hostIp

	def GenerateByNameStr(
		self,
		name: str,
		dupTester: Callable[[_IP_ADDRESS_TYPES], bool] = lambda _: False,
		dupMaxRetry: int = 100,
	) -> _IP_ADDRESS_TYPES:
		uidGen = SiteUIDGenerator(name)

		for _ in range(dupMaxRetry):
			resIp = self._GenerateFromInt(uidGen.GetUIDInt())
			if not dupTester(resIp):
				return resIp
			uidGen.NextIteration()

		raise RuntimeError(f'Failed to generate a unique IP address for {name}')

