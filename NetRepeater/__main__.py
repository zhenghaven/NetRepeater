#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# Copyright (c) 2024 Haofan Zheng
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
###


import argparse

from ModularDNS.Service import Resolver

from .DNS import ModuleManagerLoader


def GetPackageInfo() -> dict:
	import os

	thisDir = os.path.dirname(os.path.abspath(__file__))
	possibleRepoDir = os.path.dirname(thisDir)
	possibleTomlPath = os.path.join(possibleRepoDir, 'pyproject.toml')

	pkgInfo = {
		'name': __package__ or __name__,
	}

	if os.path.exists(possibleTomlPath):
		import tomllib
		with open(possibleTomlPath, 'rb') as file:
			tomlData = tomllib.load(file)
		if (
			('project' in tomlData) and
			('name' in tomlData['project']) and
			(tomlData['project']['name'] == pkgInfo['name'])
		):
			pkgInfo['description'] = tomlData['project']['description']
			pkgInfo['version'] = tomlData['project']['version']
			return pkgInfo

	import importlib
	pkgInfo['version'] = importlib.metadata.version(pkgInfo['name'])
	pkgInfo['description'] = importlib.metadata.metadata(pkgInfo['name'])['Summary']
	return pkgInfo


def main() -> int:
	pkgInfo = GetPackageInfo()

	parser = argparse.ArgumentParser(
		description=pkgInfo['description'],
	)
	parser.add_argument(
		'--version',
		action='version', version=pkgInfo['version'],
	)
	parser.add_argument(
		'--config', '-c', type=str, required=True,
		help='Path to the configuration file'
	)
	args = parser.parse_args()

	Resolver.Start(configPath=args.config)


if __name__ == '__main__':
	exit(main())

