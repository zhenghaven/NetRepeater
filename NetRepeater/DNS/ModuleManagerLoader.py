#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# Copyright (c) 2024 Haofan Zheng
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
###


from ModularDNS.ModuleManager import ModuleManager
from ModularDNS.ModuleManagerLoader import MODULE_MGR as _MOD_DNS_MODULE_MGR

from .NetRepeaterMod import ServerManagerMod


MODULE_MGR = ModuleManager()
MODULE_MGR.RegisterModule('ServerManagerMod', ServerManagerMod)


def RegisterToModuleDNS():
	_MOD_DNS_MODULE_MGR.RegisterSubModuleManager('NetRepeater', MODULE_MGR)


RegisterToModuleDNS()

