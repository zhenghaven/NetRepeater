#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# Copyright (c) 2024 Haofan Zheng
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
###


import argparse
import json
import logging

from typing import Any, Dict

from .Inbound import FindInboundServerCreator
from .Outbound import FindOutboundConnector
from . import _Meta
from . import ServerCluster


RemoteHostConfig = Dict[str, Any]
LocalProtoToRemoteHostConfig = Dict[str, RemoteHostConfig]
LocalPortToRemoteHostConfig = Dict[int, LocalProtoToRemoteHostConfig]
LocalHostToRemoteHostConfig = Dict[str, LocalPortToRemoteHostConfig]


def main() -> int:
	parser = argparse.ArgumentParser(description='Network Forwarder')
	parser.add_argument(
		'--version', action='version',
		version=f'{_Meta.__version__}'
	)
	parser.add_argument(
		'--config', '-c', type=str, required=True,
		help='Path to the configuration file'
	)
	parser.add_argument(
		'--verbose', action='store_true',
		help='Enable verbose logging'
	)
	args = parser.parse_args()

	with open(args.config, 'r') as f:
		config = json.load(f)

	logFile = None
	if 'logFile' in config:
		logFile = config['logFile']

	logLevel = logging.DEBUG if args.verbose else logging.INFO
	logFormat = '[%(asctime)s]%(levelname)s[%(name)s] - %(message)s'

	logging.basicConfig(
		level=logLevel,
		format=logFormat,
		filename=logFile
	)

	svrCluster = ServerCluster.ServerCluster()

	forwarders: LocalHostToRemoteHostConfig = config['forwarders']
	for locHost, locPort2RetHost in forwarders.items():
		for locPort, locProto2RetHost in locPort2RetHost.items():
			locPort = int(locPort)
			for locProto, retHost in locProto2RetHost.items():
				inboundServerCreator = FindInboundServerCreator(locProto)
				outboundConnector = FindOutboundConnector(retHost['proto'])
				svrCluster.AddServer(
					inboundServerCreator(
						locHost, locPort, outboundConnector(**retHost)
					)
				)

	svrCluster.ServeUntilSignals()

	return 0


if __name__ == '__main__':
	exit(main())

