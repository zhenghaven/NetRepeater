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
import socket
import subprocess
import sys
import time

from typing import Callable, Union

import netifaces

_IP_ADDRESS_TYPES   = Union[ ipaddress.IPv4Address,   ipaddress.IPv6Address   ]
_IP_INTERFACE_TYPES = Union[ ipaddress.IPv4Interface, ipaddress.IPv6Interface ]


class IPManager(object):

	_DEFAULT_ADD_RM_POLL_INTERVAL = 0.1
	_DEFAULT_BINDABLE_POLL_INTERVAL = 0.5

	@classmethod
	def IsIPBindable(
		cls,
		ip: _IP_ADDRESS_TYPES,
		logger: Union[logging.Logger, None] = None,
	) -> bool:
		if ip.version == 4:
			af = socket.AF_INET
		elif ip.version == 6:
			af = socket.AF_INET6
		else:
			raise ValueError(f'Unknown IP address version: {ip.version}')

		with socket.socket(af, socket.SOCK_STREAM) as s:
			logger.debug(f'Attempting to bind IP {ip} to socket')
			try:
				s.bind((str(ip), 0))
				# at this point, we have bound the socket with the IP
				return True
			except Exception:
				# `bind()` failed
				return False

	@classmethod
	def HasInterfaceIP(
		cls,
		ip: _IP_ADDRESS_TYPES,
		iface: str,
		logger: Union[logging.Logger, None] = None,
	) -> bool:
		ifaceAddrs = netifaces.ifaddresses(iface)

		if ip.version == 4:
			af = netifaces.AF_INET
		elif ip.version == 6:
			af = netifaces.AF_INET6
		else:
			raise ValueError(f'Unknown IP address version: {ip.version}')

		for addrObj in ifaceAddrs.get(af, []):
			if addrObj['addr'] == str(ip):
				if logger:
					logger.debug(f'Found IP {addrObj} on interface {iface}')
				return True

		return False

	@classmethod
	def WaitForCondition(
		cls,
		condition: Callable[[], bool],
		timeout: float,
		pollInterval: float,
		timeoutMsg: str = 'Waiting for condition timed out',
	) -> None:
		startTime = time.time()
		while (time.time() - startTime) < timeout:
			if condition():
				return
			time.sleep(pollInterval)
		raise TimeoutError(timeoutMsg)

	@classmethod
	def WaitInterfaceIPAdded(
		cls,
		ip: _IP_ADDRESS_TYPES,
		iface: str,
		timeout: float,
		pollInterval: float = _DEFAULT_ADD_RM_POLL_INTERVAL,
		logger: Union[logging.Logger, None] = None,
	) -> None:
		def _HasInterfaceIP() -> bool:
			return cls.HasInterfaceIP(ip, iface, logger=logger)

		cls.WaitForCondition(
			condition=_HasInterfaceIP,
			timeout=timeout,
			pollInterval=pollInterval,
			timeoutMsg=f'IP {ip} not added to interface {iface} within {timeout} seconds',
		)

	@classmethod
	def WaitInterfaceIPRemoved(
		cls,
		ip: _IP_ADDRESS_TYPES,
		iface: str,
		timeout: float,
		pollInterval: float = _DEFAULT_ADD_RM_POLL_INTERVAL,
		logger: Union[logging.Logger, None] = None,
	) -> None:
		def _HasNotInterfaceIP() -> bool:
			return not cls.HasInterfaceIP(ip, iface, logger=logger)

		cls.WaitForCondition(
			condition=_HasNotInterfaceIP,
			timeout=timeout,
			pollInterval=pollInterval,
			timeoutMsg=f'IP {ip} not removed from interface {iface} within {timeout} seconds',
		)

	@classmethod
	def WaitIPBindable(
		cls,
		ip: _IP_ADDRESS_TYPES,
		timeout: float,
		pollInterval: float = _DEFAULT_BINDABLE_POLL_INTERVAL,
		logger: Union[logging.Logger, None] = None,
	) -> None:
		def _IsIPBindable() -> bool:
			return cls.IsIPBindable(ip, logger=logger)

		cls.WaitForCondition(
			condition=_IsIPBindable,
			timeout=timeout,
			pollInterval=pollInterval,
			timeoutMsg=f'IP {ip} not bindable within {timeout} seconds',
		)

	def __init__(
		self,
		ipAndNet: _IP_INTERFACE_TYPES,
		iface: str,
	) -> None:
		super(IPManager, self).__init__()

		self.ipAndNet = ipAndNet
		self.iface = iface

		self.mode = 'not-implemented'
		self.logger = logging.getLogger(f'{__name__}.{self.__class__.__name__}')

	def AddIP(
		self,
		waitConfirm: bool = True,
	) -> None:
		raise NotImplementedError('AddIP() is not implemented')

	def RemoveIP(
		self,
		waitConfirm: bool = True,
	) -> None:
		raise NotImplementedError('RemoveIP() is not implemented')

	def _AddIP(self) -> None:
		self.logger.info(
			f'Adding IP {self.ipAndNet} to interface {self.iface} ({self.mode})'
		)

	def _RemoveIP(self) -> None:
		self.logger.info(
			f'Removing IP {self.ipAndNet} from interface {self.iface} ({self.mode})'
		)

	def HasIPAdded(self) -> bool:
		return self.HasInterfaceIP(self.ipAndNet.ip, self.iface)

	def WaitIPAdded(
		self,
		timeout: float,
		pollInterval: float = _DEFAULT_ADD_RM_POLL_INTERVAL,
	) -> None:
		self.WaitInterfaceIPAdded(
			ip=self.ipAndNet.ip,
			iface=self.iface,
			timeout=timeout,
			pollInterval=pollInterval,
			logger=self.logger,
		)

	def WaitIPRemoved(
		self,
		timeout: float,
		pollInterval: float = _DEFAULT_ADD_RM_POLL_INTERVAL,
	) -> None:
		self.WaitInterfaceIPRemoved(
			ip=self.ipAndNet.ip,
			iface=self.iface,
			timeout=timeout,
			pollInterval=pollInterval,
			logger=self.logger,
		)

	def WaitBindable(
		self,
		timeout: float,
		pollInterval: float = _DEFAULT_BINDABLE_POLL_INTERVAL,
	) -> None:
		self.WaitIPBindable(
			ip=self.ipAndNet.ip,
			timeout=timeout,
			pollInterval=pollInterval,
			logger=self.logger,
		)


class IPManagerLinux(IPManager):

	@classmethod
	def _RunSysCmd(cls, cmd: list) -> None:
		proc = subprocess.Popen(
			cmd,
			stdout=subprocess.PIPE,
			stderr=subprocess.PIPE,
		)
		outStr, errStr = proc.communicate()

		if proc.returncode != 0:
			cmdStr = ' '.join(cmd)
			raise RuntimeError(
				f'Command "{cmdStr}" failed with return code {proc.returncode} '
				f'(stdout: {outStr}, stderr: {errStr})'
			)

	@classmethod
	def _RunSysCmdToAddIP(
		cls,
		ipAndNet: _IP_INTERFACE_TYPES,
		iface: str,
	) -> None:
		ipWithPrefix = f'{ipAndNet.with_prefixlen}'

		cmd = [ 'ip', 'addr', 'add', ipWithPrefix, 'dev', str(iface) ]

		cls._RunSysCmd(cmd)

	@classmethod
	def _RunSysCmdToRemoveIP(
		cls,
		ipAndNet: _IP_INTERFACE_TYPES,
		iface: str,
	) -> None:
		ipWithPrefix = f'{ipAndNet.with_prefixlen}'

		cmd = [ 'ip', 'addr', 'del', ipWithPrefix, 'dev', str(iface) ]

		cls._RunSysCmd(cmd)

	def __init__(
		self,
		ipAndNet: _IP_INTERFACE_TYPES,
		iface: str,
	) -> None:
		super(IPManagerLinux, self).__init__(
			ipAndNet=ipAndNet,
			iface=iface,
		)

		self.mode = 'linux'

	def AddIP(
		self,
		waitConfirm: bool = True,
	) -> None:
		super(IPManagerLinux, self)._AddIP()
		if self.HasIPAdded():
			self.logger.warning(
				f'IP {self.ipAndNet} already exists on interface {self.iface}'
			)
			return
		self._RunSysCmdToAddIP(self.ipAndNet, self.iface)
		if waitConfirm:
			self.WaitIPAdded(timeout=5.0)
			# wait to ensure the address is bindable
			self.WaitBindable(timeout=5.0)

	def RemoveIP(
		self,
		waitConfirm: bool = True,
	) -> None:
		super(IPManagerLinux, self)._RemoveIP()
		if not self.HasIPAdded():
			self.logger.warning(
				f'IP {self.ipAndNet} does not exist on interface {self.iface}'
			)
			return
		self._RunSysCmdToRemoveIP(self.ipAndNet, self.iface)
		if waitConfirm:
			self.WaitIPRemoved(timeout=5.0)


class IPManagerLinuxDryRun(IPManagerLinux):

	_IP_LIST = {}

	@classmethod
	def HasInterfaceIP(
		cls,
		ip: _IP_ADDRESS_TYPES,
		iface: str,
		logger: Union[logging.Logger, None] = None,
	) -> bool:
		ifaceAddrs = cls._IP_LIST.get(iface, [])

		return ip in ifaceAddrs

	@classmethod
	def _RunSysCmd(cls, cmd: list) -> None:
		op = cmd[2]
		ipWithPrefix = cmd[3]
		iface = cmd[5]

		ip = ipaddress.ip_interface(ipWithPrefix).ip

		if op == 'add':
			if iface not in cls._IP_LIST:
				cls._IP_LIST[iface] = []
			cls._IP_LIST[iface].append(ip)
		elif op == 'del':
			cls._IP_LIST[iface].remove(ip)
		else:
			raise ValueError(f'Unknown operation: {op}')

	def __init__(
		self,
		ipAndNet: _IP_INTERFACE_TYPES,
		iface: str,
	) -> None:
		super(IPManagerLinuxDryRun, self).__init__(
			ipAndNet=ipAndNet,
			iface=iface,
		)

		self.mode = 'linux-dry-run'


_IP_MANAGER_TYPES = {
	'linux'         : IPManagerLinux,
	'linux-dry-run' : IPManagerLinuxDryRun,
}


def CreateIPManager(
	mode: str,
	ipAndNet: _IP_INTERFACE_TYPES,
	iface: str,
) -> IPManager:
	mgrCls = _IP_MANAGER_TYPES[mode]

	return mgrCls(
		ipAndNet=ipAndNet,
		iface=iface,
	)


def DetectType() -> str:
	if sys.platform.startswith('linux'):
		return 'linux'
	else:
		raise RuntimeError(f'Unsupported platform: {sys.platform}')

