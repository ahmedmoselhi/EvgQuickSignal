#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  plugin.py
#  
#  Copyright 2022 Evg77734
#  

from Plugins.Plugin import PluginDescriptor
from .EvgQuickSignal import onstart0

version = 'ver. 1.3'
	
def main(session, **kwargs):
	onstart0(session)

def Plugins(path, **kwargs):
	return PluginDescriptor(name = _("EvgQuickSignal") + str(version), where = [PluginDescriptor.WHERE_PLUGINMENU], description = _("EvgQuickSignal from Evg77734"), icon = 'evgquicksignal.png', fnc = main)
