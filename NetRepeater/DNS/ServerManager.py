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

from typing import List, Tuple, Union

from CacheLib.LockwSLD import LockwSLD
from CacheLib.TTL.Interfaces import KeyValueItem, KeyValueKey, Terminable
from CacheLib.TTL.MultiKeyUniTTLValueCache import MultiKeyUniTTLValueCache

from ModularDNS.Downstream.QuickLookup import QuickLookup as _IPAddrLookup

from ..Inbound.FindCreator import FindServerCreator
from ..Inbound.LegacyServer import Server
from ..Outbound.FindCreator import FindConnector
from ..Outbound.Handler import HandlerConnector
from ..Utils.IfaceSetup.IPManager import CreateIPManager
from ..Utils.RandIPGenerator import RandIPGenerator


_IP_ADDRESS_TYPES   = Union[ ipaddress.IPv4Address,   ipaddress.IPv6Address   ]
_IP_NETWORK_TYPES   = Union[ ipaddress.IPv4Network,   ipaddress.IPv6Network   ]
_IP_INTERFACE_TYPES = Union[ ipaddress.IPv4Interface, ipaddress.IPv6Interface ]


def CreateServerWithRemoteHostName(
	proto: str,
	localHost: _IP_ADDRESS_TYPES,
	localPort: int,
	remoteHost: str,
	remotePort: int,
	remoteIPLookup: _IPAddrLookup,
	remotePreferIPv6: bool,
) -> Server:
	def _ipLookup(hostname: str) -> _IP_ADDRESS_TYPES:
		return remoteIPLookup.LookupIpAddr(
			domain=hostname,
			recDepthStack=[],
			preferIPv6=remotePreferIPv6
		)

	inSvrCreator = FindServerCreator(proto)
	outConnectorCls = FindConnector(proto)['dynamic']

	connector: HandlerConnector = outConnectorCls(
		hostName=remoteHost,
		port=remotePort,
		addrLookup=_ipLookup,
	)

	server: Server = inSvrCreator(
		address=localHost,
		port=localPort,
		handlerConnector=connector,
	)

	return server


class ServiceItem(KeyValueItem):
	def __init__(
		self,
		localIpAndNet: _IP_INTERFACE_TYPES,
		localPort: int,
		localIface: str,
		localIfaceMode: str,
		proto: str,
		remoteHost: str,
		remotePort: int,
		remoteIPLookup: _IPAddrLookup,
		remotePreferIPv6: bool,
	) -> None:
		super(ServiceItem, self).__init__()

		self._localIpAndNet  = localIpAndNet
		self._localPort      = localPort
		self._localIface     = localIface
		self._localIfaceMode = localIfaceMode

		self._proto            = proto

		self._remoteHost       = remoteHost
		self._remotePort       = remotePort
		self._remoteIPLookup   = remoteIPLookup
		self._remotePreferIPv6 = remotePreferIPv6

		# create server
		self._server = CreateServerWithRemoteHostName(
			proto=self._proto,
			localHost=self._localIpAndNet.ip,
			localPort=self._localPort,
			remoteHost=self._remoteHost,
			remotePort=self._remotePort,
			remoteIPLookup=self._remoteIPLookup,
			remotePreferIPv6=self._remotePreferIPv6,
		)
		self._server.ThreadedServeUntilTerminate()

	def GetKeys(self) -> List[KeyValueKey]:
		return [
			self._localIpAndNet.ip,
			self._remoteHost,
		]

	def Terminate(self) -> None:
		# terminate the server
		self._server.Terminate()

	def GetServerPort(self) -> int:
		return self._server.server_address[1]

	def GetServerIP(self) -> _IP_ADDRESS_TYPES:
		return self._localIpAndNet.ip


class ServerItem(KeyValueItem):
	def __init__(
		self,
		localIpAndNet: _IP_INTERFACE_TYPES,
		localIface: str,
		localIfaceMode: str,
		protoAndPorts: List[Union[Tuple[str, int, int], Tuple[str, int]]],
		remoteHost: str,
		remoteIPLookup: _IPAddrLookup,
		remotePreferIPv6: bool = False,
	) -> None:
		super(ServerItem, self).__init__()

		self._localIpAndNet  = localIpAndNet
		self._localIface     = localIface
		self._localIfaceMode = localIfaceMode

		self._remoteHost       = remoteHost
		self._remoteIPLookup   = remoteIPLookup
		self._remotePreferIPv6 = remotePreferIPv6

		self._protoAndPorts = protoAndPorts

		# setup network interfaces
		self._ipMgr = CreateIPManager(
			mode=self._localIfaceMode,
			ipAndNet=self._localIpAndNet,
			iface=self._localIface,
		)
		self._ipMgr.AddIP(waitConfirm=True)

		# create services
		self._services: List[ServiceItem] = []
		for protoPort in self._protoAndPorts:
			if len(protoPort) == 2:
				proto, localPort = protoPort
				remotePort = localPort
			elif len(protoPort) == 3:
				proto, localPort, remotePort = protoPort
			else:
				raise ValueError('Invalid argument for protocol and port')

			service = ServiceItem(
				localIpAndNet=self._localIpAndNet,
				localPort=localPort,
				localIface=self._localIface,
				localIfaceMode=self._localIfaceMode,
				proto=proto,
				remoteHost=self._remoteHost,
				remotePort=remotePort,
				remoteIPLookup=self._remoteIPLookup,
				remotePreferIPv6=self._remotePreferIPv6,
			)
			self._services.append(service)

	def GetKeys(self) -> List[KeyValueKey]:
		return [
			self._localIpAndNet.ip,
			self._remoteHost,
		]

	def Terminate(self) -> None:
		# terminate the services
		for service in self._services:
			service.Terminate()

		# remove network interfaces
		self._ipMgr.RemoveIP(waitConfirm=True)

	def GetServerIP(self) -> _IP_ADDRESS_TYPES:
		return self._localIpAndNet.ip


class ServerManager(Terminable):

	def __init__(
		self,
		localNet: _IP_NETWORK_TYPES,
		localIface: str,
		localIfaceMode: str,
		protoAndPorts: List[Union[Tuple[str, int, int], Tuple[str, int]]],
		remoteIPLookup: _IPAddrLookup,
		serverTTL: Tuple[int, str],
		remotePreferIPv6: bool = False,
	) -> None:
		super(ServerManager, self).__init__()

		self._localNet       = localNet
		self._localIface     = localIface
		self._localIfaceMode = localIfaceMode

		self._protoAndPorts  = protoAndPorts

		self._remoteIPLookup   = remoteIPLookup
		self._remotePreferIPv6 = remotePreferIPv6

		self._serverTTL = serverTTL

		self._randIpGen = RandIPGenerator(
			network=self._localNet,
		)

		self._cacheLock = LockwSLD()
		self._cache = MultiKeyUniTTLValueCache(ttl=self._serverTTL)

		self._logger = logging.getLogger(
			f'{__name__}.{self.__class__.__name__}'
		)

	def _DoesIPInUseLockHeld(self, ip: _IP_ADDRESS_TYPES) -> bool:
		return ip in self._cache

	def _DoesServerExistLockHeld(self, hostName) -> bool:
		return hostName in self._cache

	def _LookupOrCreateServerLockHeld(self, hostName: str) -> ServerItem:
		if self._DoesServerExistLockHeld(hostName):
			# server already exists
			serverItem: ServerItem = self._cache.Get(hostName)
			return serverItem
		else:
			# server does not exist
			# create a new server

			# check if the domain name is valid via DNS lookup
			# if not, an exception will be raised here
			_ = self._remoteIPLookup.LookupIpAddr(
				domain=hostName,
				recDepthStack=[],
				preferIPv6=self._remotePreferIPv6,
			)

			# generate a random IP address
			randIP = self._randIpGen.GenerateByNameStr(
				name=hostName,
				dupTester=self._DoesIPInUseLockHeld,
			)
			localIpAndNet = ipaddress.ip_interface(
				f'{randIP}/{self._localNet.prefixlen}'
			)

			self._logger.debug(
				f'Creating a new server for {hostName} at {randIP}'
			)

			# create a server item
			serverItem = ServerItem(
				localIpAndNet=localIpAndNet,
				localIface=self._localIface,
				localIfaceMode=self._localIfaceMode,
				protoAndPorts=self._protoAndPorts,
				remoteHost=hostName,
				remoteIPLookup=self._remoteIPLookup,
				remotePreferIPv6=self._remotePreferIPv6,
			)
			# try to put the server item into the cache
			try:
				self._cache.Put(serverItem)
			except Exception:
				serverItem.Terminate()
				raise
			# at this point, the ownership of the server item is transferred
			# to the cache

			self._logger.info(
				f'Created a new server for {hostName} at {randIP}'
			)

			# return the server item
			return serverItem

	def LookupOrCreateServer(self, hostName: str) -> _IP_ADDRESS_TYPES:
		with self._cacheLock:
			serverItem = self._LookupOrCreateServerLockHeld(hostName)
			return serverItem.GetServerIP()

	def Terminate(self) -> None:
		# terminate all servers
		with self._cacheLock:
			self._cache.Terminate()

