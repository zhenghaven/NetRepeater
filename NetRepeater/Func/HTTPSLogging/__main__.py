#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# Copyright (c) 2025 Haofan Zheng
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
###


import argparse
import json
import logging
import os

from ModularDNS import Logger
from ModularDNS.SignalHandler import WaitUntilSignals
from ModularDNS.Downstream.DownstreamCollection import DownstreamCollection
from ModularDNS.ModuleManagerLoader import MODULE_MGR as ROOT_MODULE_MGR

from ...Downstream.Handler.HandlerManager import BuildHandlerDictFromConfig
from ...Inbound.Server.ConfigReader import CreateServerFromConfig


def Start(configPath: os.PathLike) -> None:

	with open(configPath, 'r') as f:
		config = json.load(f)

	Logger.InitializeFromConfig(config.get('logger', {}))
	logger = logging.getLogger(f'{__name__}.{Start.__name__}')

	downstreamConfig = config['downstream']
	middlewaresConfig = config['middlewares']
	serverConfig = config['servers']

	with DownstreamCollection.FromConfig(
		moduleMgr=ROOT_MODULE_MGR,
		config=downstreamConfig,
	) as dCollection:
		logger.info('Downstream Collection initialized.')

		for middleware in middlewaresConfig:
			assert middleware['module'] == 'http_logging', \
				'Only http_logging middleware is supported in this example.'
			middleware['config']['dnsCollection'] = dCollection
		logger.info('Initializing Middlewares...')
		middlewareHdlr = BuildHandlerDictFromConfig(middlewaresConfig)

		logger.info('Initializing Servers...')
		servers = CreateServerFromConfig(
			config=serverConfig,
			downstreamHandlerDict=middlewareHdlr,
		)

		try:
			logger.info('Starting Servers...')
			for server in servers:
				server.ThreadedServeUntilTerminate()

			WaitUntilSignals().Wait()
		finally:
			for server in servers:
				server.Terminate()

	logger.info('Servers terminated.')


def main() -> None:
	parser = argparse.ArgumentParser(
		description='NetRepeater HTTPS Logging',
	)
	parser.add_argument(
		'--config',
		type=str,
		required=True,
		help='Path to the configuration file',
	)
	args = parser.parse_args()

	configPath = args.config
	Start(configPath)


if __name__ == '__main__':
	main()

