#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# Copyright (c) 2025 Haofan Zheng
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
###


import base64
import datetime
import gzip
import json
import random
import os
import requests
import threading

from typing import Callable, TypeVar

from ModularDNS.Downstream.DownstreamCollection import (
	DownstreamCollection as _DNSDownstreamCollection
)
from ModularDNS.Downstream.QuickLookup import QuickLookup as _BaseQuickLookup

from PyNetworkLib.Server.HTTP.DownstreamHandlerBase import DownstreamHandlerBase
from PyNetworkLib.Server.HTTP.PyHandlerBase import PyHandlerBase
from PyNetworkLib.Server.HTTP.Utils.HostField import HOST_FIELD_TYPES
from PyNetworkLib.Server.Utils.HandlerState import HandlerState

from .HandlerDict import HandlerBase, HandlerDict


_SessionStateAnyT = TypeVar('_SessionStateAnyT')


class HTTPLoggingHandler(DownstreamHandlerBase, HandlerBase):

	@classmethod
	def FromConfig(
		cls,
		handlersDict: HandlerDict,
		*,
		dnsCollection: _DNSDownstreamCollection,
		dnsQuickLookup: str,
		destDomain: str,
		loggingDir: os.PathLike,
		preferIPv6: bool = False,
		tlsVerifyPeer: bool = True,
		proto: str = 'https',
	) -> 'HTTPLoggingHandler':
		return cls(
			dnsQuickLookup=dnsCollection.GetQuickLookup(dnsQuickLookup),
			destDomain=destDomain,
			loggingDir=loggingDir,
			preferIPv6=preferIPv6,
			tlsVerifyPeer=tlsVerifyPeer,
			proto=proto,
		)

	def __init__(
		self,
		dnsQuickLookup: _BaseQuickLookup,
		destDomain: str,
		loggingDir: os.PathLike,
		preferIPv6: bool = False,
		tlsVerifyPeer: bool = True,
		proto: str = 'https',
	) -> None:
		super().__init__()

		self._dnsQuickLookup = dnsQuickLookup
		self._destDomain = destDomain
		self._loggingDir = loggingDir
		self._preferIPv6 = preferIPv6
		self._tlsVerifyPeer = tlsVerifyPeer
		self._proto = proto

		if not os.path.isdir(self._loggingDir):
			raise ValueError(
				f'Logging directory "{self._loggingDir}" does not exist or is not a directory.'
			)

	def _GetSessionAttr(
		self,
		pyHandler: PyHandlerBase,
		attrName: str,
		defaultCreator: Callable[[], _SessionStateAnyT]
	) -> _SessionStateAnyT:
		if hasattr(pyHandler, attrName):
			# this is not the first request in this session
			# use the existing session state
			st: _SessionStateAnyT = getattr(pyHandler, attrName)
		else:
			# this is the first request in this session
			# create a new session state
			st = defaultCreator()
			setattr(pyHandler, attrName, st)

		return st

	def _GenLogID(self) -> str:
		'''
		Generate a unique log ID for the request.

		Format: `YYYYMMDD_HHMMSSMMM_<8 random alphanumeric characters>`
		'''
		now = datetime.datetime.now()
		timestamp = now.strftime('%Y%m%d_%H%M%S%f')
		random_suffix = ''.join(
			random.choices(
				'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
				k=8
			)
		)
		return f'{timestamp}_{random_suffix}'

	def _LogCommunication(
		self,
		reqRelPath: str,
		reqPath: str,
		reqMethod: str,
		reqHeaders: dict,
		reqBody: str,
		respCode: int,
		respHeaders: list[list[str]],
		respBody: str,
		respContent: str,
	) -> None:
		logID = self._GenLogID()
		logFilePath = os.path.join(self._loggingDir, f'{logID}.log.json')
		logData = {
			'logID': logID,
			'timestamp': datetime.datetime.now().isoformat(),
			'requestRelativePath': reqRelPath,
			'requestPath': reqPath,
			'requestMethod': reqMethod,
			'requestHeaders': reqHeaders,
			'requestBody': reqBody,
			'responseCode': respCode,
			'responseHeaders': respHeaders,
			'responseBody': respBody,
			'responseContent': respContent,
		}
		with open(logFilePath, 'w', encoding='utf-8') as logFile:
			json.dump(logData, logFile, ensure_ascii=False, indent='\t')

	def HandleRequest(
		self,
		*, # required that all parameters are keyword-only
		host: HOST_FIELD_TYPES,
		relPath: str,
		pyHandler: PyHandlerBase,
		handlerState: HandlerState,
		reqState: dict,
		terminateEvent: threading.Event,
	) -> None:
		reqSess = self._GetSessionAttr(
			pyHandler,
			'downstreamReqSession',
			lambda: requests.Session()
		)
		destIP = self._GetSessionAttr(
			pyHandler,
			'downstreamDestIP',
			lambda: self._dnsQuickLookup.LookupIpAddr(
				domain=self._destDomain,
				recDepthStack=[],
				preferIPv6=self._preferIPv6,
			)
		)

		# capture the request details
		reqMethod = pyHandler.command.upper()
		reqPath = str(pyHandler.path)
		if not reqPath.startswith('/'):
			reqPath = '/' + reqPath
		reqHeaders = {
			k: v for k, v in pyHandler.headers.items()
		}
		reqBody = None
		if pyHandler.body is not None:
			reqBody = pyHandler.body.decode('utf-8', errors='replace')

		# forward the request to the destination server
		resp = reqSess.request(
			method=reqMethod,
			url=f'{self._proto}://{destIP}/{reqPath[1:]}',
			headers={
				'Host': self._destDomain,
				**{k: v for k, v in reqHeaders.items() if k.lower() != 'host'}
			},
			data=reqBody,
			verify=self._tlsVerifyPeer,
			stream=True,
		)

		# capture the response details
		respCode = resp.status_code
		respHeaders = [
			[k, v] for k, v in resp.headers.items()
		]
		respRawBody = resp.raw.read()
		respRawBodyB64 = base64.b64encode(respRawBody).decode('utf-8')

		if resp.headers.get('Content-Encoding') == 'gzip':
			# if the response is gzipped, decode it
			respContent = gzip.decompress(respRawBody).decode('utf-8', errors='replace')
		else:
			# otherwise, use the raw body
			respContent = respRawBody.decode('utf-8', errors='replace')

		# log the communication
		self._LogCommunication(
			reqRelPath=relPath,
			reqPath=reqPath,
			reqMethod=reqMethod,
			reqHeaders=reqHeaders,
			reqBody=reqBody,
			respCode=respCode,
			respHeaders=respHeaders,
			respBody=respRawBodyB64,
			respContent=respContent,
		)

		# send the response back to the client
		pyHandler.SetStatusCode(respCode)
		for header, value in respHeaders:
			if header.lower() == 'transfer-encoding' and value.lower() == 'chunked':
				# skip chunked transfer encoding header
				continue
			pyHandler.AddResponseHeader(header, value)
		if respRawBody is not None:
			pyHandler.SetResponseBody(respRawBody)
