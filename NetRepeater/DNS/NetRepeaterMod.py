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

import dns.rdata
import dns.rdataclass
import dns.rdatatype

from ModularDNS import Exceptions as _DNSExceptions
from ModularDNS.Downstream.DownstreamCollection import (
	DownstreamCollection as _DNSDownstreamCollection
)
from ModularDNS.Downstream.QuickLookup import QuickLookup as _BaseQuickLookup
from ModularDNS.MsgEntry.AnsEntry import AnsEntry as _DNSAnsEntry
from ModularDNS.MsgEntry.MsgEntry import MsgEntry as _DNSMsgEntry
from ModularDNS.MsgEntry.QuestionEntry import QuestionEntry as _DNSQuestionEntry

from .ServerManager import (
	ServerManager,
	_IP_NETWORK_TYPES,
)
from ..Utils.IfaceSetup.IPManager import DetectType as _IPManagerDetectType

class ServerManagerMod(_BaseQuickLookup):

	@classmethod
	def FromConfig(
		cls,
		dCollection: _DNSDownstreamCollection,
		localNet: str,
		localIface: str,
		protoAndPorts: List[list],
		remoteIPLookup: str,
		serverTTL: list,
		remotePreferIPv6: bool = False,
		**kwargs,
	) -> 'ServerManagerMod':
		localNet = ipaddress.ip_network(localNet)

		if 'localIfaceMode' in kwargs:
			localIfaceMode = kwargs['localIfaceMode']
			# remove the key from kwargs
			del kwargs['localIfaceMode']
		else:
			localIfaceMode = _IPManagerDetectType()

		checkedProtoAndPorts = []
		for protoPort in protoAndPorts:
			if len(protoPort) == 2:
				checkedProtoAndPorts.append(
					(str(protoPort[0]), int(protoPort[1]))
				)
			elif len(protoPort) == 3:
				checkedProtoAndPorts.append(
					(str(protoPort[0]), int(protoPort[1]), int(protoPort[2]))
				)
			else:
				raise ValueError(f'Invalid protocol and port config: {protoPort}')

		remoteIPLookup = dCollection.GetQuickLookup(remoteIPLookup)

		serverTTL = (int(serverTTL[0]), str(serverTTL[1]))

		if serverTTL[1] not in ['s', 'm', 'h', 'd']:
			raise ValueError(f'Invalid TTL unit: {serverTTL[1]}')
		if serverTTL[0] <= 0:
			raise ValueError(f'Invalid TTL value: {serverTTL[0]}')

		if serverTTL[1] == 'd':
			serverTTL = (serverTTL[0] * 24, 'h')
		if serverTTL[1] == 'h':
			serverTTL = (serverTTL[0] * 60, 'm')
		if serverTTL[1] == 'm':
			serverTTL = (serverTTL[0] * 60, 's')

		return cls(
			localNet=localNet,
			localIface=localIface,
			localIfaceMode=localIfaceMode,
			protoAndPorts=checkedProtoAndPorts,
			remoteIPLookup=remoteIPLookup,
			serverTTL=serverTTL,
			remotePreferIPv6=remotePreferIPv6,
		)

	def __init__(
		self,
		localNet: _IP_NETWORK_TYPES,
		localIface: str,
		localIfaceMode: str,
		protoAndPorts: List[Union[Tuple[str, int, int], Tuple[str, int]]],
		remoteIPLookup: _BaseQuickLookup,
		serverTTL: Tuple[int, str],
		remotePreferIPv6: bool = False,
	) -> None:
		super(ServerManagerMod, self).__init__()

		self._serverManager = ServerManager(
			localNet=localNet,
			localIface=localIface,
			localIfaceMode=localIfaceMode,
			protoAndPorts=protoAndPorts,
			remoteIPLookup=remoteIPLookup,
			serverTTL=serverTTL,
			remotePreferIPv6=remotePreferIPv6,
		)

		if localNet.version == 4:
			self._supportedRDType = dns.rdatatype.A
		elif localNet.version == 6:
			self._supportedRDType = dns.rdatatype.AAAA
		else:
			raise ValueError(f'Unknown IP address version: {localNet.version}')

		self._ansTTL = 60

		self._logger = logging.getLogger(f'{__name__}.{self.__class__.__name__}')

	def HandleQuestion(
		self,
		msgEntry: _DNSQuestionEntry,
		senderAddr: Tuple[str, int],
		recDepthStack: List[ Tuple[ int, str ] ],
	) -> List[ _DNSMsgEntry ]:
		newRecStack = self.CheckRecursionDepth(
			recDepthStack,
			self.HandleQuestion
		)

		domain = msgEntry.GetNameStr(omitFinalDot=True)

		if msgEntry.rdCls != dns.rdataclass.IN:
			# we don't support other classes
			self._logger.debug(f'Unsupported class: {dns.rdataclass.to_text(msgEntry.rdCls)}')
			raise _DNSExceptions.DNSNameNotFoundError(domain, 'NetRepeaterMod')

		if msgEntry.rdType not in [dns.rdatatype.A, dns.rdatatype.AAAA]:
			# we don't support other types
			self._logger.debug(f'Unsupported type: {dns.rdatatype.to_text(msgEntry.rdType)}')
			raise _DNSExceptions.DNSNameNotFoundError(domain, 'NetRepeaterMod')

		repeaterIP = self._serverManager.LookupOrCreateServer(domain)

		ans = _DNSAnsEntry(
			name=msgEntry.name,
			rdCls=msgEntry.rdCls,
			rdType=self._supportedRDType,
			dataList=[
				dns.rdata.from_text(
					rdclass=msgEntry.rdCls,
					rdtype=self._supportedRDType,
					tok=str(repeaterIP),
				)
			],
			ttl=self._ansTTL,
		)

		return [ ans ]

	def Terminate(self) -> None:
		self._serverManager.Terminate()

