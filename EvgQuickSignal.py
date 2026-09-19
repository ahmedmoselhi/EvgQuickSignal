from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.Sensors import sensors
from GlobalActions import globalActionMap
from enigma import eConsoleAppContainer, iServiceInformation, getDesktop, eTimer, iPlayableService
from os import listdir, popen
from Components.Sources.StaticText import StaticText
from enigma import ePoint, iPlayableService
from Components.ServiceEventTracker import ServiceEventTracker
from Tools.Directories import pathExists, fileExists
from .bitrate import Bitrate
from Components.Pixmap import Pixmap
import os
import re
from .screens.skin import *
from Screens.ChannelSelection import ChannelSelection
from Components.NimManager import nimmanager, getConfigSatlist
from Components.ConfigList import ConfigListScreen
from Components.config import config, getConfigListEntry, ConfigSelection, ConfigSubsection, ConfigYesNo, configfile, NoSave
from os import path
from enigma import iServiceInformation, iPlayableService, iPlayableServicePtr, eServiceReference, eEPGCache, eServiceCenter
from threading import Thread
import time
import socket
version = ' ver. 1.3'
def getsnr():
    if os.path.exists('/tmp/snr.dat') == True:
        try:
            with open('/tmp/snr.dat', 'r', errors='ignore') as file:
                contents = file.readlines()
                snr1 = str(contents[0])
            snr11 = snr1.rstrip()
            file.close()
        except:
            snr11 = '0'
    else:
        snr11 = '0'
    return snr11
def getagc():
    if os.path.exists('/tmp/agc.dat') == True:
        try:
            with open('/tmp/agc.dat', 'r', errors='ignore') as file:
                contents = file.readlines()
                snr1 = str(contents[0])
            snr11 = snr1.rstrip()
            file.close()
        except:
            snr11 = '0'
    else:
        snr11 = '0'
    return snr11
class EvgQuickSignalSAT(Screen):
    sz_w = getDesktop(0).size().width()
    if sz_w == 1920:
        skin = EQSSAT_HD
    def __init__(self, session, args=0):
        self.session = session
        Screen.__init__(self, session)
        self['tit'] = StaticText(_('EvgQuickSignal') + str(version))
        self['key_tuner0'] = StaticText(' ')
        self['key_tuner1'] = StaticText(' ')
        self['key_tuner2'] = StaticText(' ')
        self['key_DiSEqC0'] = StaticText(' ')
        self['key_DiSEqC1'] = StaticText(' ')
        self['key_DiSEqC2'] = StaticText(' ')
        self['key_DiSEqC10'] = StaticText(' ')
        self['key_DiSEqC11'] = StaticText(' ')
        self['key_DiSEqC12'] = StaticText(' ')
        self['key_lnb0'] = StaticText(' ')
        self['key_lnb1'] = StaticText(' ')
        self['key_lnb2'] = StaticText(' ')
        self['key_sat0'] = StaticText(' ')
        self['key_sat1'] = StaticText(' ')
        self['key_sat2'] = StaticText(' ')
        self['key_T2'] = StaticText(' ')
        self.onstart()
        self['actions'] = ActionMap(['OkCancelActions', 'DirectionActions', 'HelpActions', 'EPGSelectActions', 'ShortcutActions', 'WizardActions', 'ColorActions', 'MenuActions'], {'cancel': self.Exit, 'info': self.about, 'ok': self.OK, 'blue': self.bluebutton}, (-1))
    def bluebutton(self):
        self.session.open(EvgQuickSignalBitrate)
    def OK(self):
        self.session.open(EvgQuickSignalSATAnalog)
    def onstart(self):
        self.nim_slots = []
        try:
            nimfile = open('/proc/bus/nim_sockets', 'r', errors='ignore')
        except IOError:
            return
        current_slot = None
        entries = {}
        for line in nimfile:
            if not line:
                break
            else:
                line = line.strip()
                if line.startswith('NIM Socket'):
                    parts = line.split(' ')
                    current_slot = int(parts[2][:(-1)])
                    entries[current_slot] = {}
                else:
                    if line.startswith('Type:'):
                        entries[current_slot]['type'] = str(line[6:])
                        entries[current_slot]['isempty'] = False
                    else:
                        if line.strip().startswith('Input_Name:'):
                            entries[current_slot]['input_name'] = str(line.strip()[12:])
                        else:
                            if line.startswith('Name:'):
                                entries[current_slot]['name'] = str(line[6:])
                                entries[current_slot]['isempty'] = False
                            else:
                                if line.startswith('Has_Outputs:'):
                                    input = str(line[len('Has_Outputs:') + 1:])
                                    entries[current_slot]['has_outputs'] = input == 'yes'
                                else:
                                    if line.startswith('Internally_Connectable:'):
                                        input = int(line[len('Internally_Connectable:') + 1:])
                                        entries[current_slot]['internally_connectable'] = input
                                    else:
                                        if line.startswith('Supports_Blind_Scan:'):
                                            input = str(line[len('Supports_Blind_Scan:') + 1:])
                                            entries[current_slot]['supports_blind_scan'] = input == 'yes'
                                        else:
                                            if line.startswith('Frontend_Device:'):
                                                input = int(line[len('Frontend_Device:') + 1:])
                                                entries[current_slot]['frontend_device'] = input
                                            else:
                                                if line.startswith('Mode'):
                                                    split = line.split(':')
                                                    split[1] = split[1].replace(' ', '')
                                                    split2 = split[0].split(' ')
                                                    modes = entries[current_slot].get('multi_type', {})
                                                    modes[split2[1]] = split[1]
                                                    entries[current_slot]['multi_type'] = modes
                                                else:
                                                    if line.startswith('I2C_Device:'):
                                                        input = int(line[len('I2C_Device:') + 1:])
                                                        entries[current_slot]['i2c'] = input
                                                    else:
                                                        if line.startswith('empty'):
                                                            entries[current_slot]['type'] = None
                                                            entries[current_slot]['name'] = _('N/A')
                                                            entries[current_slot]['isempty'] = True
        nimfile.close()
        n = 0
        ta1 = ' '
        ta2 = ' '
        tb1 = ' '
        tb2 = ' '
        for id, entry in entries.items():
            if not ('name' in entry and 'type' in entry):
                entry['name'] = _('N/A')
                entry['type'] = None
            if 'i2c' not in entry:
                entry['i2c'] = None
            if 'has_outputs' not in entry:
                entry['has_outputs'] = True
            if 'frontend_device' in entry:
                if path.exists('/proc/stb/frontend/%d/rf_switch' % entry['frontend_device']) and (id > 0 or getBoxType() == 'vusolo2'):
                    entry['internally_connectable'] = entry['frontend_device'] - 1
                else:
                    entry['internally_connectable'] = None
            else:
                entry['frontend_device'] = entry['internally_connectable'] = None
            if 'multi_type' not in entry:
                if entry['name'] == 'DVB-T2/C USB-Stick':
                    entry['multi_type'] = {'0': 'DVB-T'}
                    entry['multi_type'] = {'1': 'DVB-C'}
                else:
                    entry['multi_type'] = {}
            if 'input_name' not in entry:
                entry['input_name'] = chr(ord('A') + id)
            if 'supports_blind_scan' not in entry:
                entry['supports_blind_scan'] = False
            if n == 0:
                ta1 = str(entry['name'])
                ta2 = '(' + str(entry['type']) + ')'
            if n == 1:
                tb1 = str(entry['name'])
                tb2 = '(' + str(entry['type']) + ')'
            n = n + 1
        tunera = ta1
        tunera1 = ta2
        tunerb = tb1
        tunerb1 = tb2
        service = self.session.nav.getCurrentService()
        info = service and service.info()
        orbital_pos = 0
        tunertype = ' '
        orbitalpos = 0
        orbitalpos1 = 'n/a'
        if info is not None:
            xresol = info.getInfo(iServiceInformation.sVideoWidth)
            yresol = info.getInfo(iServiceInformation.sVideoHeight)
            feinfo = service and service.frontendInfo()
            if feinfo is not None:
                frontendData = feinfo and feinfo.getAll(True)
                if frontendData is not None:
                    if frontendData.get('tuner_type') == 'DVB-S':
                        orbital_pos = int(frontendData['orbital_position'])
                        if orbital_pos > 1800:
                            orbitalpos = 3600 - orbital_pos
                            tunertype = frontendData.get('tuner_type')
                            orbitalpos1 = str(float(3600 - orbital_pos) / 10.0) + 'W'
                        else:
                            if orbital_pos > 0:
                                orbitalpos = orbital_pos
                                tunertype = frontendData.get('tuner_type')
                                orbitalpos1 = str(float(orbital_pos) / 10.0) + 'E'
                    if frontendData.get('tuner_type') == 'DVB-T':
                        tunertype = frontendData.get('tuner_type')
        n = 0
        try:
            if n == 0:
                self['key_tuner0'].setText('Tuner')
                self['key_tuner1'].setText(str(tunera))
                self['key_tuner2'].setText(str(tunera1))
                try:
                    T = int(config.Nims[n].dvbs.advanced.sat[orbitalpos].lnb.value)
                except:
                    T = 0
                if config.Nims[n].dvbs.advanced.lnb[T].diseqcMode.value == '1_1' or config.Nims[n].dvbs.advanced.lnb[T].diseqcMode.value == '1_2':
                    S = str(config.Nims[n].dvbs.advanced.lnb[T].diseqcMode.value)
                    S1 = S[0] + '.' + S[2]
                    self['key_DiSEqC0'].setText('DiSEqC ' + str(S1))
                    self['key_DiSEqC1'].setText('Port')
                    self['key_DiSEqC2'].setText(str(config.Nims[n].dvbs.advanced.lnb[T].uncommittedDiseqcCommand.value))
                    self['key_DiSEqC10'].setText('DiSEqC 1.0')
                    self['key_DiSEqC11'].setText('Port')
                    S2 = config.Nims[n].dvbs.advanced.lnb[T].commitedDiseqcCommand.value
                    if S2 == 'AA':
                        S2 = 'A'
                    if S2 == 'AB':
                        S2 = 'B'
                    if S2 == 'BA':
                        S2 = 'C'
                    if S2 == 'BB':
                        S2 = 'D'
                    self['key_DiSEqC12'].setText(str(S2))
                    self['key_lnb0'].setText('LNB')
                    self['key_lnb2'].setText(str(config.Nims[n].dvbs.advanced.sat[orbitalpos].lnb.value))
                    self['key_sat0'].setText('Satellite')
                    self['key_sat2'].setText(str(orbitalpos1))
                if config.Nims[n].dvbs.advanced.lnb[T].diseqcMode.value == '1_0':
                    S = str(config.Nims[n].dvbs.advanced.lnb[T].diseqcMode.value)
                    S1 = S[0] + '.' + S[2]
                    self['key_DiSEqC0'].setText('DiSEqC 1.1')
                    self['key_DiSEqC1'].setText('Port')
                    self['key_DiSEqC2'].setText('none')
                    self['key_DiSEqC10'].setText('DiSEqC ' + str(S1))
                    self['key_DiSEqC11'].setText('Port')
                    S2 = config.Nims[n].dvbs.advanced.lnb[T].commitedDiseqcCommand.value
                    if S2 == 'AA':
                        S2 = 'A'
                    if S2 == 'AB':
                        S2 = 'B'
                    if S2 == 'BA':
                        S2 = 'C'
                    if S2 == 'BB':
                        S2 = 'D'
                    self['key_DiSEqC12'].setText(str(S2))
                    self['key_lnb0'].setText('LNB')
                    self['key_lnb2'].setText(str(config.Nims[n].dvbs.advanced.sat[orbitalpos].lnb.value))
                    self['key_sat0'].setText('Satellite')
                    self['key_sat2'].setText(str(orbitalpos1))
        except:
            self['key_lnb0'].setText('LNB')
            self['key_lnb2'].setText('1')
            self['key_sat0'].setText('Satellite')
            self['key_sat2'].setText(str(orbitalpos1))
    def about(self):
        self.session.open(MessageBox, 'EvgQuickSignal' + str(version) + _(' (py3)\n\nDeveloper: Evg77734\n\nHomepage: gisclub.tv'), MessageBox.TYPE_INFO)
    def Exit(self):
        self.close()
class EvgQuickSignalSATAnalog(Screen):
    sz_w = getDesktop(0).size().width()
    if sz_w == 1920:
        skin = EQSSATANALOG_HD
    def __init__(self, session, args=0):
        self.session = session
        Screen.__init__(self, session)
        self['tit'] = StaticText(_('EvgQuickSignal') + str(version))
        self['key_tuner0'] = StaticText(' ')
        self['key_tuner1'] = StaticText(' ')
        self['key_tuner2'] = StaticText(' ')
        self['key_DiSEqC0'] = StaticText(' ')
        self['key_DiSEqC1'] = StaticText(' ')
        self['key_DiSEqC2'] = StaticText(' ')
        self['key_DiSEqC10'] = StaticText(' ')
        self['key_DiSEqC11'] = StaticText(' ')
        self['key_DiSEqC12'] = StaticText(' ')
        self['key_lnb0'] = StaticText(' ')
        self['key_lnb1'] = StaticText(' ')
        self['key_lnb2'] = StaticText(' ')
        self['key_sat0'] = StaticText(' ')
        self['key_sat1'] = StaticText(' ')
        self['key_sat2'] = StaticText(' ')
        self['key_T2'] = StaticText(' ')
        self['snr'] = Pixmap()
        self['agc'] = Pixmap()
        self.n = 0
        self.m = int(getsnr())
        self.n1 = 0
        self.m1 = int(getagc())
        self.onstart()
        self['actions'] = ActionMap(['OkCancelActions', 'DirectionActions', 'HelpActions', 'EPGSelectActions', 'ShortcutActions', 'WizardActions', 'ColorActions', 'MenuActions'], {'ok': self.OK}, (-1))
        self.onShow.append(self.setPosition)
        Thread0 = Thread(target=self.startarrow1)
        Thread0.start()
        Thread00 = Thread(target=self.startarrow2)
        Thread00.start()
        Thread1 = Thread(target=self.snr)
        Thread1.start()
        Thread2 = Thread(target=self.agc)
        Thread2.start()
    def setPosition(self):
        self['snr'].move(ePoint(845, 259))
        self['snr'].instance.setPixmapFromFile('/usr/lib/enigma2/python/Plugins/Extensions/EvgQuickSignal/arrow/a0.png')
        self['snr'].instance.show()
        self['agc'].move(ePoint(1450, 259))
        self['agc'].instance.setPixmapFromFile('/usr/lib/enigma2/python/Plugins/Extensions/EvgQuickSignal/arrow/a0.png')
        self['agc'].instance.show()
    def OK(self):
        self.close()
    def startarrow1(self):
        self.moveTimer0 = eTimer()
        self.moveTimer0.callback.append(self.movePosition0)
        self.moveTimer0.start(10, 1)
    def movePosition0(self):
        self.moveTimer0.start(20, 1)
        self.m = int(getsnr())
        self['snr'].move(ePoint(845, 259))
        self['snr'].instance.setPixmapFromFile('/usr/lib/enigma2/python/Plugins/Extensions/EvgQuickSignal/arrow/a' + str(self.n) + '.png')
        self['snr'].instance.show()
        if self.n >= self.m:
            self.moveTimer0.stop()
            self.n = 0
        self.n = self.n + 1
    def startarrow2(self):
        self.moveTimer00 = eTimer()
        self.moveTimer00.callback.append(self.movePosition00)
        self.moveTimer00.start(10, 1)
    def movePosition00(self):
        self.moveTimer00.start(20, 1)
        self.m1 = int(getagc())
        self['agc'].move(ePoint(1450, 259))
        self['agc'].instance.setPixmapFromFile('/usr/lib/enigma2/python/Plugins/Extensions/EvgQuickSignal/arrow/a' + str(self.n1) + '.png')
        self['agc'].instance.show()
        if self.n1 >= self.m1:
            self.moveTimer00.stop()
            self.n1 = 0
        self.n1 = self.n1 + 1
    def snr(self):
        self.moveTimer1 = eTimer()
        self.moveTimer1.callback.append(self.movePosition1)
        self.moveTimer1.start(2000, 1)
    def movePosition1(self):
        self.moveTimer1.start(100, 1)
        self['snr'].move(ePoint(845, 259))
        self['snr'].instance.setPixmapFromFile('/usr/lib/enigma2/python/Plugins/Extensions/EvgQuickSignal/arrow/a' + str(getsnr()) + '.png')
        self['snr'].instance.show()
    def agc(self):
        self.moveTimer2 = eTimer()
        self.moveTimer2.callback.append(self.movePosition2)
        self.moveTimer2.start(2000, 1)
    def movePosition2(self):
        self.moveTimer2.start(100, 1)
        self['agc'].move(ePoint(1450, 259))
        self['agc'].instance.setPixmapFromFile('/usr/lib/enigma2/python/Plugins/Extensions/EvgQuickSignal/arrow/a' + str(getagc()) + '.png')
        self['agc'].instance.show()
    def onstart(self):
        self.nim_slots = []
        try:
            nimfile = open('/proc/bus/nim_sockets', 'r', errors='ignore')
        except IOError:
            return
        current_slot = None
        entries = {}
        for line in nimfile:
            if not line:
                break
            else:
                line = line.strip()
                if line.startswith('NIM Socket'):
                    parts = line.split(' ')
                    current_slot = int(parts[2][:(-1)])
                    entries[current_slot] = {}
                else:
                    if line.startswith('Type:'):
                        entries[current_slot]['type'] = str(line[6:])
                        entries[current_slot]['isempty'] = False
                    else:
                        if line.strip().startswith('Input_Name:'):
                            entries[current_slot]['input_name'] = str(line.strip()[12:])
                        else:
                            if line.startswith('Name:'):
                                entries[current_slot]['name'] = str(line[6:])
                                entries[current_slot]['isempty'] = False
                            else:
                                if line.startswith('Has_Outputs:'):
                                    input = str(line[len('Has_Outputs:') + 1:])
                                    entries[current_slot]['has_outputs'] = input == 'yes'
                                else:
                                    if line.startswith('Internally_Connectable:'):
                                        input = int(line[len('Internally_Connectable:') + 1:])
                                        entries[current_slot]['internally_connectable'] = input
                                    else:
                                        if line.startswith('Supports_Blind_Scan:'):
                                            input = str(line[len('Supports_Blind_Scan:') + 1:])
                                            entries[current_slot]['supports_blind_scan'] = input == 'yes'
                                        else:
                                            if line.startswith('Frontend_Device:'):
                                                input = int(line[len('Frontend_Device:') + 1:])
                                                entries[current_slot]['frontend_device'] = input
                                            else:
                                                if line.startswith('Mode'):
                                                    split = line.split(':')
                                                    split[1] = split[1].replace(' ', '')
                                                    split2 = split[0].split(' ')
                                                    modes = entries[current_slot].get('multi_type', {})
                                                    modes[split2[1]] = split[1]
                                                    entries[current_slot]['multi_type'] = modes
                                                else:
                                                    if line.startswith('I2C_Device:'):
                                                        input = int(line[len('I2C_Device:') + 1:])
                                                        entries[current_slot]['i2c'] = input
                                                    else:
                                                        if line.startswith('empty'):
                                                            entries[current_slot]['type'] = None
                                                            entries[current_slot]['name'] = _('N/A')
                                                            entries[current_slot]['isempty'] = True
        nimfile.close()
        n = 0
        ta1 = ' '
        ta2 = ' '
        tb1 = ' '
        tb2 = ' '
        for id, entry in entries.items():
            if not ('name' in entry and 'type' in entry):
                entry['name'] = _('N/A')
                entry['type'] = None
            if 'i2c' not in entry:
                entry['i2c'] = None
            if 'has_outputs' not in entry:
                entry['has_outputs'] = True
            if 'frontend_device' in entry:
                if path.exists('/proc/stb/frontend/%d/rf_switch' % entry['frontend_device']) and (id > 0 or getBoxType() == 'vusolo2'):
                    entry['internally_connectable'] = entry['frontend_device'] - 1
                else:
                    entry['internally_connectable'] = None
            else:
                entry['frontend_device'] = entry['internally_connectable'] = None
            if 'multi_type' not in entry:
                if entry['name'] == 'DVB-T2/C USB-Stick':
                    entry['multi_type'] = {'0': 'DVB-T'}
                    entry['multi_type'] = {'1': 'DVB-C'}
                else:
                    entry['multi_type'] = {}
            if 'input_name' not in entry:
                entry['input_name'] = chr(ord('A') + id)
            if 'supports_blind_scan' not in entry:
                entry['supports_blind_scan'] = False
            if n == 0:
                ta1 = str(entry['name'])
                ta2 = '(' + str(entry['type']) + ')'
            if n == 1:
                tb1 = str(entry['name'])
                tb2 = '(' + str(entry['type']) + ')'
            n = n + 1
        tunera = ta1
        tunera1 = ta2
        tunerb = tb1
        tunerb1 = tb2
        service = self.session.nav.getCurrentService()
        info = service and service.info()
        orbital_pos = 0
        tunertype = ' '
        orbitalpos = 0
        orbitalpos1 = 'n/a'
        if info is not None:
            xresol = info.getInfo(iServiceInformation.sVideoWidth)
            yresol = info.getInfo(iServiceInformation.sVideoHeight)
            feinfo = service and service.frontendInfo()
            if feinfo is not None:
                frontendData = feinfo and feinfo.getAll(True)
                if frontendData is not None:
                    if frontendData.get('tuner_type') == 'DVB-S':
                        orbital_pos = int(frontendData['orbital_position'])
                        if orbital_pos > 1800:
                            orbitalpos = 3600 - orbital_pos
                            tunertype = frontendData.get('tuner_type')
                            orbitalpos1 = str(float(3600 - orbital_pos) / 10.0) + 'W'
                        else:
                            if orbital_pos > 0:
                                orbitalpos = orbital_pos
                                tunertype = frontendData.get('tuner_type')
                                orbitalpos1 = str(float(orbital_pos) / 10.0) + 'E'
                    if frontendData.get('tuner_type') == 'DVB-T':
                        tunertype = frontendData.get('tuner_type')
        n = 0
        try:
            if n == 0:
                self['key_tuner0'].setText('Tuner')
                self['key_tuner1'].setText(str(tunera))
                self['key_tuner2'].setText(str(tunera1))
                try:
                    T = int(config.Nims[n].dvbs.advanced.sat[orbitalpos].lnb.value)
                except:
                    T = 0
                if config.Nims[n].dvbs.advanced.lnb[T].diseqcMode.value == '1_1' or config.Nims[n].dvbs.advanced.lnb[T].diseqcMode.value == '1_2':
                    S = str(config.Nims[n].dvbs.advanced.lnb[T].diseqcMode.value)
                    S1 = S[0] + '.' + S[2]
                    self['key_DiSEqC0'].setText('DiSEqC ' + str(S1))
                    self['key_DiSEqC1'].setText('Port')
                    self['key_DiSEqC2'].setText(str(config.Nims[n].dvbs.advanced.lnb[T].uncommittedDiseqcCommand.value))
                    self['key_DiSEqC10'].setText('DiSEqC 1.0')
                    self['key_DiSEqC11'].setText('Port')
                    S2 = config.Nims[n].dvbs.advanced.lnb[T].commitedDiseqcCommand.value
                    if S2 == 'AA':
                        S2 = 'A'
                    if S2 == 'AB':
                        S2 = 'B'
                    if S2 == 'BA':
                        S2 = 'C'
                    if S2 == 'BB':
                        S2 = 'D'
                    self['key_DiSEqC12'].setText(str(S2))
                    self['key_lnb0'].setText('LNB')
                    self['key_lnb2'].setText(str(config.Nims[n].dvbs.advanced.sat[orbitalpos].lnb.value))
                    self['key_sat0'].setText('Satellite')
                    self['key_sat2'].setText(str(orbitalpos1))
                if config.Nims[n].dvbs.advanced.lnb[T].diseqcMode.value == '1_0':
                    S = str(config.Nims[n].dvbs.advanced.lnb[T].diseqcMode.value)
                    S1 = S[0] + '.' + S[2]
                    self['key_DiSEqC0'].setText('DiSEqC 1.1')
                    self['key_DiSEqC1'].setText('Port')
                    self['key_DiSEqC2'].setText('none')
                    self['key_DiSEqC10'].setText('DiSEqC ' + str(S1))
                    self['key_DiSEqC11'].setText('Port')
                    S2 = config.Nims[n].dvbs.advanced.lnb[T].commitedDiseqcCommand.value
                    if S2 == 'AA':
                        S2 = 'A'
                    if S2 == 'AB':
                        S2 = 'B'
                    if S2 == 'BA':
                        S2 = 'C'
                    if S2 == 'BB':
                        S2 = 'D'
                    self['key_DiSEqC12'].setText(str(S2))
                    self['key_lnb0'].setText('LNB')
                    self['key_lnb2'].setText(str(config.Nims[n].dvbs.advanced.sat[orbitalpos].lnb.value))
                    self['key_sat0'].setText('Satellite')
                    self['key_sat2'].setText(str(orbitalpos1))
        except:
            self['key_lnb0'].setText('LNB')
            self['key_lnb2'].setText('1')
            self['key_sat0'].setText('Satellite')
            self['key_sat2'].setText(str(orbitalpos1))
class EvgQuickSignalT2(Screen):
    sz_w = getDesktop(0).size().width()
    if sz_w == 1920:
        skin = EQST2_HD
    def __init__(self, session, args=0):
        self.session = session
        Screen.__init__(self, session)
        self['tit'] = StaticText(_('EvgQuickSignal') + str(version))
        self['key_tuner0'] = StaticText(' ')
        self['key_tuner1'] = StaticText(' ')
        self['key_tuner2'] = StaticText(' ')
        self['key_sat0'] = StaticText(' ')
        self['key_sat1'] = StaticText(' ')
        self['key_sat2'] = StaticText(' ')
        self['key_T2'] = StaticText(' ')
        self.onstart()
        self['actions'] = ActionMap(['OkCancelActions', 'DirectionActions', 'HelpActions', 'EPGSelectActions', 'ColorActions'], {'cancel': self.Exit, 'info': self.about, 'ok': self.OK, 'blue': self.bluebutton}, (-1))
    def bluebutton(self):
        self.session.open(EvgQuickSignalBitrate)
    def OK(self):
        self.session.open(EvgQuickSignalT2Analog)
    def onstart(self):
        self.nim_slots = []
        try:
            nimfile = open('/proc/bus/nim_sockets', 'r', errors='ignore')
        except IOError:
            return
        current_slot = None
        entries = {}
        for line in nimfile:
            if not line:
                break
            else:
                line = line.strip()
                if line.startswith('NIM Socket'):
                    parts = line.split(' ')
                    current_slot = int(parts[2][:(-1)])
                    entries[current_slot] = {}
                else:
                    if line.startswith('Type:'):
                        entries[current_slot]['type'] = str(line[6:])
                        entries[current_slot]['isempty'] = False
                    else:
                        if line.strip().startswith('Input_Name:'):
                            entries[current_slot]['input_name'] = str(line.strip()[12:])
                        else:
                            if line.startswith('Name:'):
                                entries[current_slot]['name'] = str(line[6:])
                                entries[current_slot]['isempty'] = False
                            else:
                                if line.startswith('Has_Outputs:'):
                                    input = str(line[len('Has_Outputs:') + 1:])
                                    entries[current_slot]['has_outputs'] = input == 'yes'
                                else:
                                    if line.startswith('Internally_Connectable:'):
                                        input = int(line[len('Internally_Connectable:') + 1:])
                                        entries[current_slot]['internally_connectable'] = input
                                    else:
                                        if line.startswith('Supports_Blind_Scan:'):
                                            input = str(line[len('Supports_Blind_Scan:') + 1:])
                                            entries[current_slot]['supports_blind_scan'] = input == 'yes'
                                        else:
                                            if line.startswith('Frontend_Device:'):
                                                input = int(line[len('Frontend_Device:') + 1:])
                                                entries[current_slot]['frontend_device'] = input
                                            else:
                                                if line.startswith('Mode'):
                                                    split = line.split(':')
                                                    split[1] = split[1].replace(' ', '')
                                                    split2 = split[0].split(' ')
                                                    modes = entries[current_slot].get('multi_type', {})
                                                    modes[split2[1]] = split[1]
                                                    entries[current_slot]['multi_type'] = modes
                                                else:
                                                    if line.startswith('I2C_Device:'):
                                                        input = int(line[len('I2C_Device:') + 1:])
                                                        entries[current_slot]['i2c'] = input
                                                    else:
                                                        if line.startswith('empty'):
                                                            entries[current_slot]['type'] = None
                                                            entries[current_slot]['name'] = _('N/A')
                                                            entries[current_slot]['isempty'] = True
        nimfile.close()
        n = 0
        ta1 = ' '
        ta2 = ' '
        tb1 = ' '
        tb2 = ' '
        for id, entry in entries.items():
            if not ('name' in entry and 'type' in entry):
                entry['name'] = _('N/A')
                entry['type'] = None
            if 'i2c' not in entry:
                entry['i2c'] = None
            if 'has_outputs' not in entry:
                entry['has_outputs'] = True
            if 'frontend_device' in entry:
                if path.exists('/proc/stb/frontend/%d/rf_switch' % entry['frontend_device']) and (id > 0 or getBoxType() == 'vusolo2'):
                    entry['internally_connectable'] = entry['frontend_device'] - 1
                else:
                    entry['internally_connectable'] = None
            else:
                entry['frontend_device'] = entry['internally_connectable'] = None
            if 'multi_type' not in entry:
                if entry['name'] == 'DVB-T2/C USB-Stick':
                    entry['multi_type'] = {'0': 'DVB-T'}
                    entry['multi_type'] = {'1': 'DVB-C'}
                else:
                    entry['multi_type'] = {}
            if 'input_name' not in entry:
                entry['input_name'] = chr(ord('A') + id)
            if 'supports_blind_scan' not in entry:
                entry['supports_blind_scan'] = False
            if n == 0:
                ta1 = str(entry['name'])
                ta2 = '(' + str(entry['type']) + ')'
            if n == 1:
                tb1 = str(entry['name'])
                tb2 = '(' + str(entry['type']) + ')'
            n = n + 1
        tunera = ta1
        tunera1 = ta2
        tunerb = tb1
        tunerb1 = tb2
        self['key_tuner0'].setText('Tuner')
        self['key_tuner1'].setText(str(tunerb))
        self['key_tuner2'].setText(str(tunerb1))
        T = str(config.Nims[1].dvbt.terrestrial.value)
        self['key_T2'].setText(str(T))
        self['key_sat0'].setText('Tower')
        self['key_sat1'].setText('transmitter')
        self['key_sat2'].setText('DVB-T2')
    def about(self):
        self.session.open(MessageBox, 'EvgQuickSignal' + str(version) + _(' (py3)\n\nDeveloper: Evg77734\n\nHomepage: gisclub.tv'), MessageBox.TYPE_INFO)
    def Exit(self):
        self.close()
class EvgQuickSignalT2MI(Screen):
    sz_w = getDesktop(0).size().width()
    if sz_w == 1920:
        skin = EQST2MI_HD
    def __init__(self, session, args=0):
        self.session = session
        Screen.__init__(self, session)
        self['tit'] = StaticText(_('EvgQuickSignal') + str(version))
        self['sat'] = StaticText(' ')
        self['frek'] = StaticText(' ')
        self['sid'] = StaticText(' ')
        self['plp'] = StaticText(' ')
        self['str'] = StaticText(' ')
        self['astrasm'] = StaticText(' ')
        self.n = 0
        self.Data_Text = ''
        self.t = 0
        self.k = 19
        self.newstr2 = []
        self.onstart()
        self['actions'] = ActionMap(['OkCancelActions', 'DirectionActions', 'HelpActions', 'EPGSelectActions', 'ColorActions'], {'cancel': self.Exit, 'info': self.about, 'blue': self.bluebutton}, (-1))
        self.SysUpdateTimer = eTimer()
        self.SysUpdateTimer.callback.append(self.updateSysInfo)
        self.onLayoutFinish.append(self.DataReader)
    def searchInfoFiles(self):
        lfile = '/tmp/astra.log'
        if os.path.exists(lfile) == True:
            with open(lfile, 'r', errors='ignore') as f:
                count = sum((1 for _ in f))
            f = open(lfile, 'r', errors='ignore')
            data_lines = f.readlines()
            f.close()
            newstr = []
            for i in data_lines:
                newstr.append(i.rstrip())
            countstr = []
            n = 1
            while n < len(newstr):
                if '(*)' in newstr[n]:
                    countstr.append(n)
                n = n + 1
            if len(countstr) > 0:
                m = countstr[len(countstr) - 1] - 1
            else:
                m = 0
            while m < count:
                self.newstr2.append(newstr[m])
                m = m + 1
    def DataReader(self):
        self.searchInfoFiles()
        self.updateSysInfo()
        self.SysUpdateTimer.start(200)
    def updateSysInfo(self):
        try:
            m = self.t
            self.Data_Text = ''
            while m < self.k:
                self.Data_Text = self.Data_Text + '\n' + self.newstr2[m]
                m = m + 1
            self['str'].setText(str(self.Data_Text))
            self.t = self.t + 1
            self.k = self.k + 1
        except:
            pass
    def bluebutton(self):
        self.session.open(EvgQuickSignalBitrate)
    def onstart(self):
        if os.path.exists('/tmp/ref2.info') == True:
            try:
                with open('/tmp/ref2.info', 'r', errors='ignore') as file:
                    contents = file.readlines()
                    ref = str(contents[0])
                S = ref.rstrip()
                file.close()
            except:
                S = ' '
        else:
            S = ' '
        try:
            S_clean = S.replace('%3a', ':').replace('%3A', ':')
            parts = S_clean.split(':')
            
            if len(parts) >= 4 and parts[3]:
                try:
                    sid1 = int(parts[3], 16)
                    self['sid'].setText(str(sid1))
                except:
                    self['sid'].setText(' ')
            else:
                self['sid'].setText(' ')

            found_freq = ''
            found_sat = ''
            found_plp = ''

            match = re.search(r'(\d{3,5})[_\s]+(\d+\.?\d*)\s*([weWE])(?:[_\s]*plp(\d+))?', S_clean, re.IGNORECASE)
            if match:
                found_freq = match.group(1) + ' MHz'
                sat_val = match.group(2)
                sat_dir = match.group(3).upper()
                found_sat = f"{sat_val} {sat_dir}"
                if match.group(4) is not None:
                    found_plp = match.group(4)

            if not found_plp:
                plp_match = re.search(r'plp:?\s*(\d+)', S_clean, re.IGNORECASE)
                if plp_match:
                    found_plp = plp_match.group(1)

            if not found_sat and len(parts) >= 7 and parts[6]:
                try:
                    namespace = int(parts[6], 16)
                    orb_pos = (namespace >> 16) & 0xFFFF
                    if orb_pos > 0:
                        if orb_pos > 1800:
                            found_sat = f"{(3600 - orb_pos)/10.0} W"
                        else:
                            found_sat = f"{orb_pos/10.0} E"
                except:
                    pass

            if found_sat:
                self['sat'].setText(found_sat)
            else:
                self['sat'].setText(' ')

            if found_freq:
                self['frek'].setText(found_freq)
            else:
                self['frek'].setText(' ')

            if found_plp:
                self['plp'].setText('PLP: ' + str(found_plp) + ' - T2MI')
            else:
                self['plp'].setText(' ')
        except:
            self['sid'].setText(' ')
            self['frek'].setText(' ')
            self['sat'].setText(' ')
            self['plp'].setText(' ')
            
        path = '/var/lib/opkg/'
        contents = []
        if os.path.exists(path + 'status') == True:
            with open(path + 'status', 'r', errors='ignore') as file:
                contents = file.readlines()
            file.close()
        newstr = []
        for i in contents:
            newstr.append(i.rstrip())
        cc = 'n/a'
        m = 0
        while m < len(newstr):
            if newstr[m].startswith('Package: astra-sm'):
                cc = str(newstr[m + 1])
                break
            m = m + 1
        aa = 'No time'
        if os.path.exists('/var/run/astra.pid') == True:
            aa = time.ctime(os.path.getmtime('/var/run/astra.pid'))
        self['astrasm'].setText('astra-sm ' + str(cc) + '  ' + str(aa))
    def about(self):
        self.session.open(MessageBox, 'EvgQuickSignal' + str(version) + _(' (py3)\n\nDeveloper: Evg77734\n\nHomepage: gisclub.tv'), MessageBox.TYPE_INFO)
    def Exit(self):
        self.close()
class EvgQuickSignalIPCAM(Screen):
    sz_w = getDesktop(0).size().width()
    if sz_w == 1920:
        skin = EQSIPCAM_HD
    def __init__(self, session, args=0):
        self.session = session
        Screen.__init__(self, session)
        self['tit'] = StaticText(_('EvgQuickSignal') + str(version))
        self['bouquet'] = StaticText(' ')
        self['channel'] = StaticText(' ')
        self['ref'] = StaticText(' ')
        self['frek'] = StaticText(' ')
        self['sid'] = StaticText(' ')
        self['ipcam'] = StaticText(' ')
        self['protocol'] = StaticText(' ')
        self['login'] = StaticText(' ')
        self['pass'] = StaticText(' ')
        self['iplocal'] = StaticText(' ')
        self['cam'] = Pixmap()
        self.onstart()
        self['actions'] = ActionMap(['OkCancelActions', 'DirectionActions', 'HelpActions', 'EPGSelectActions'], {'cancel': self.Exit, 'info': self.about}, (-1))
        self.onShow.append(self.setPosition)
    def setPosition(self):
        self['cam'].move(ePoint(910, 183))
        self['cam'].instance.setPixmapFromFile('/usr/lib/enigma2/python/Plugins/Extensions/EvgQuickSignal/images/cam.png')
        self['cam'].instance.show()
    def onstart(self):
        if os.path.exists('/tmp/ref3.info') == True:
            try:
                with open('/tmp/ref3.info', 'r', errors='ignore') as file:
                    contents = file.readlines()
                    d0 = str(contents[0])
                    d1 = str(contents[1])
                    d2 = str(contents[2])
                    d3 = str(contents[3])
                    d4 = str(contents[4])
                    d5 = str(contents[5])
                    d6 = str(contents[6])
                    d7 = str(contents[7])
                    d8 = str(contents[8])
                    d9 = str(contents[9])
                d00 = d0.rstrip()
                d11 = d1.rstrip()
                d22 = d2.rstrip()
                d33 = d3.rstrip()
                d44 = d4.rstrip()
                d55 = d5.rstrip()
                d66 = d6.rstrip()
                d77 = d7.rstrip()
                d88 = d8.rstrip()
                d99 = d9.rstrip()
                file.close()
            except:
                d00 = ' '
                d11 = ' '
                d22 = ' '
                d33 = ' '
                d44 = ' '
                d55 = ' '
                d66 = ' '
                d77 = ' '
                d88 = ' '
                d99 = ' '
        else:
            d00 = ' '
            d11 = ' '
            d22 = ' '
            d33 = ' '
            d44 = ' '
            d55 = ' '
            d66 = ' '
            d77 = ' '
            d88 = ' '
            d99 = ' '
        self['bouquet'].setText(str(d11))
        self['channel'].setText(str(d22))
        self['ref'].setText(str(d33))
        self['frek'].setText(str(d44))
        self['sid'].setText(str(d55))
        self['ipcam'].setText(str(d66))
        self['protocol'].setText(str(d77))
        self['login'].setText(str(d88))
        self['pass'].setText(str(d99))
        gw = os.popen('ip -4 route show default').read().split()
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect((gw[2], 0))
        ipaddr = s.getsockname()[0]
        self['iplocal'].setText(str(ipaddr))
    def about(self):
        self.session.open(MessageBox, 'EvgQuickSignal' + str(version) + _(' (py3)\n\nDeveloper: Evg77734\n\nHomepage: gisclub.tv'), MessageBox.TYPE_INFO)
    def Exit(self):
        self.close()
class EvgQuickSignalIPTV(Screen):
    sz_w = getDesktop(0).size().width()
    if sz_w == 1920:
        skin = EQSIPTV_HD
    def __init__(self, session, args=0):
        self.session = session
        Screen.__init__(self, session)
        self['tit'] = StaticText(_('EvgQuickSignal') + str(version))
        self['key_tuner0'] = StaticText(' ')
        self['key_tuner1'] = StaticText(' ')
        self['key_tuner2'] = StaticText(' ')
        self['key_sat0'] = StaticText(' ')
        self['key_sat1'] = StaticText(' ')
        self['key_sat2'] = StaticText(' ')
        self['key_T2'] = StaticText(' ')
        self.onstart()
        self['actions'] = ActionMap(['OkCancelActions', 'DirectionActions', 'HelpActions', 'EPGSelectActions'], {'cancel': self.Exit, 'info': self.about}, (-1))
    def onstart(self):
        z = 7
    def about(self):
        self.session.open(MessageBox, 'EvgQuickSignal' + str(version) + _(' (py3)\n\nDeveloper: Evg77734\n\nHomepage: gisclub.tv'), MessageBox.TYPE_INFO)
    def Exit(self):
        self.close()
class EvgQuickSignalHDSkin(Screen):
    skin = EvgQuickSignalHDSkin
    def __init__(self, session, args=0):
        self.session = session
        Screen.__init__(self, session)
        self['tears'] = Pixmap()
        self.tears = 0
        self.onstart()
        self['actions'] = ActionMap(['OkCancelActions', 'DirectionActions', 'HelpActions', 'EPGSelectActions'], {'cancel': self.Exit}, (-1))
        self.onShow.append(self.setPosition)
        Thread4 = Thread(target=self.tears1)
        Thread4.start()
    def setPosition(self):
        self['tears'].move(ePoint(50, 50))
        self['tears'].instance.setPixmapFromFile('/usr/lib/enigma2/python/Plugins/Extensions/EvgQuickSignal/tears/frame-1_1.png')
        self['tears'].instance.show()
    def tears1(self):
        self.moveTimer4 = eTimer()
        self.moveTimer4.callback.append(self.movePosition4)
        self.moveTimer4.start(500, 1)
    def movePosition4(self):
        self.moveTimer4.start(75, 1)
        self.tears = self.tears + 1
        if self.tears >= 49:
            self.tears = 1
        self['tears'].move(ePoint(50, 50))
        self['tears'].instance.setPixmapFromFile('/usr/lib/enigma2/python/Plugins/Extensions/EvgQuickSignal/tears/frame-' + str(self.tears) + '_1.png')
        self['tears'].instance.show()
    def onstart(self):
        z = 7
    def Exit(self):
        self.close()
class EvgQuickSignalT2Analog(Screen):
    sz_w = getDesktop(0).size().width()
    if sz_w == 1920:
        skin = EQST2Analog_HD
    def __init__(self, session, args=0):
        self.session = session
        Screen.__init__(self, session)
        self['tit'] = StaticText(_('EvgQuickSignal') + str(version))
        self['key_tuner0'] = StaticText(' ')
        self['key_tuner1'] = StaticText(' ')
        self['key_tuner2'] = StaticText(' ')
        self['key_sat0'] = StaticText(' ')
        self['key_sat1'] = StaticText(' ')
        self['key_sat2'] = StaticText(' ')
        self['key_T2'] = StaticText(' ')
        self['snr'] = Pixmap()
        self['agc'] = Pixmap()
        self.n = 0
        self.m = int(getsnr())
        self.n1 = 0
        self.m1 = int(getagc())
        self.onstart()
        self['actions'] = ActionMap(['OkCancelActions', 'DirectionActions', 'HelpActions', 'EPGSelectActions'], {'ok': self.OK}, (-1))
        self.onShow.append(self.setPosition)
        Thread0 = Thread(target=self.startarrow1)
        Thread0.start()
        Thread00 = Thread(target=self.startarrow2)
        Thread00.start()
        Thread1 = Thread(target=self.snr)
        Thread1.start()
        Thread2 = Thread(target=self.agc)
        Thread2.start()
    def setPosition(self):
        self['snr'].move(ePoint(845, 259))
        self['snr'].instance.setPixmapFromFile('/usr/lib/enigma2/python/Plugins/Extensions/EvgQuickSignal/arrow/a0.png')
        self['snr'].instance.show()
        self['agc'].move(ePoint(1450, 259))
        self['agc'].instance.setPixmapFromFile('/usr/lib/enigma2/python/Plugins/Extensions/EvgQuickSignal/arrow/a0.png')
        self['agc'].instance.show()
    def startarrow1(self):
        self.moveTimer0 = eTimer()
        self.moveTimer0.callback.append(self.movePosition0)
        self.moveTimer0.start(10, 1)
    def movePosition0(self):
        self.moveTimer0.start(20, 1)
        self.m = int(getsnr())
        self['snr'].move(ePoint(845, 259))
        self['snr'].instance.setPixmapFromFile('/usr/lib/enigma2/python/Plugins/Extensions/EvgQuickSignal/arrow/a' + str(self.n) + '.png')
        self['snr'].instance.show()
        if self.n >= self.m:
            self.moveTimer0.stop()
            self.n = 0
        self.n = self.n + 1
    def startarrow2(self):
        self.moveTimer00 = eTimer()
        self.moveTimer00.callback.append(self.movePosition00)
        self.moveTimer00.start(10, 1)
    def movePosition00(self):
        self.moveTimer00.start(20, 1)
        self.m1 = int(getagc())
        self['agc'].move(ePoint(1450, 259))
        self['agc'].instance.setPixmapFromFile('/usr/lib/enigma2/python/Plugins/Extensions/EvgQuickSignal/arrow/a' + str(self.n1) + '.png')
        self['agc'].instance.show()
        if self.n1 >= self.m1:
            self.moveTimer00.stop()
            self.n1 = 0
        self.n1 = self.n1 + 1
    def snr(self):
        self.moveTimer1 = eTimer()
        self.moveTimer1.callback.append(self.movePosition1)
        self.moveTimer1.start(2000, 1)
    def movePosition1(self):
        self.moveTimer1.start(100, 1)
        self['snr'].move(ePoint(845, 259))
        self['snr'].instance.setPixmapFromFile('/usr/lib/enigma2/python/Plugins/Extensions/EvgQuickSignal/arrow/a' + str(getsnr()) + '.png')
        self['snr'].instance.show()
    def agc(self):
        self.moveTimer2 = eTimer()
        self.moveTimer2.callback.append(self.movePosition2)
        self.moveTimer2.start(2000, 1)
    def movePosition2(self):
        self.moveTimer2.start(100, 1)
        self['agc'].move(ePoint(1450, 259))
        self['agc'].instance.setPixmapFromFile('/usr/lib/enigma2/python/Plugins/Extensions/EvgQuickSignal/arrow/a' + str(getagc()) + '.png')
        self['agc'].instance.show()
    def onstart(self):
        self.nim_slots = []
        try:
            nimfile = open('/proc/bus/nim_sockets', 'r', errors='ignore')
        except IOError:
            return
        current_slot = None
        entries = {}
        for line in nimfile:
            if not line:
                break
            else:
                line = line.strip()
                if line.startswith('NIM Socket'):
                    parts = line.split(' ')
                    current_slot = int(parts[2][:(-1)])
                    entries[current_slot] = {}
                else:
                    if line.startswith('Type:'):
                        entries[current_slot]['type'] = str(line[6:])
                        entries[current_slot]['isempty'] = False
                    else:
                        if line.strip().startswith('Input_Name:'):
                            entries[current_slot]['input_name'] = str(line.strip()[12:])
                        else:
                            if line.startswith('Name:'):
                                entries[current_slot]['name'] = str(line[6:])
                                entries[current_slot]['isempty'] = False
                            else:
                                if line.startswith('Has_Outputs:'):
                                    input = str(line[len('Has_Outputs:') + 1:])
                                    entries[current_slot]['has_outputs'] = input == 'yes'
                                else:
                                    if line.startswith('Internally_Connectable:'):
                                        input = int(line[len('Internally_Connectable:') + 1:])
                                        entries[current_slot]['internally_connectable'] = input
                                    else:
                                        if line.startswith('Supports_Blind_Scan:'):
                                            input = str(line[len('Supports_Blind_Scan:') + 1:])
                                            entries[current_slot]['supports_blind_scan'] = input == 'yes'
                                        else:
                                            if line.startswith('Frontend_Device:'):
                                                input = int(line[len('Frontend_Device:') + 1:])
                                                entries[current_slot]['frontend_device'] = input
                                            else:
                                                if line.startswith('Mode'):
                                                    split = line.split(':')
                                                    split[1] = split[1].replace(' ', '')
                                                    split2 = split[0].split(' ')
                                                    modes = entries[current_slot].get('multi_type', {})
                                                    modes[split2[1]] = split[1]
                                                    entries[current_slot]['multi_type'] = modes
                                                else:
                                                    if line.startswith('I2C_Device:'):
                                                        input = int(line[len('I2C_Device:') + 1:])
                                                        entries[current_slot]['i2c'] = input
                                                    else:
                                                        if line.startswith('empty'):
                                                            entries[current_slot]['type'] = None
                                                            entries[current_slot]['name'] = _('N/A')
                                                            entries[current_slot]['isempty'] = True
        nimfile.close()
        n = 0
        ta1 = ' '
        ta2 = ' '
        tb1 = ' '
        tb2 = ' '
        for id, entry in entries.items():
            if not ('name' in entry and 'type' in entry):
                entry['name'] = _('N/A')
                entry['type'] = None
            if 'i2c' not in entry:
                entry['i2c'] = None
            if 'has_outputs' not in entry:
                entry['has_outputs'] = True
            if 'frontend_device' in entry:
                if path.exists('/proc/stb/frontend/%d/rf_switch' % entry['frontend_device']) and (id > 0 or getBoxType() == 'vusolo2'):
                    entry['internally_connectable'] = entry['frontend_device'] - 1
                else:
                    entry['internally_connectable'] = None
            else:
                entry['frontend_device'] = entry['internally_connectable'] = None
            if 'multi_type' not in entry:
                if entry['name'] == 'DVB-T2/C USB-Stick':
                    entry['multi_type'] = {'0': 'DVB-T'}
                    entry['multi_type'] = {'1': 'DVB-C'}
                else:
                    entry['multi_type'] = {}
            if 'input_name' not in entry:
                entry['input_name'] = chr(ord('A') + id)
            if 'supports_blind_scan' not in entry:
                entry['supports_blind_scan'] = False
            if n == 0:
                ta1 = str(entry['name'])
                ta2 = '(' + str(entry['type']) + ')'
            if n == 1:
                tb1 = str(entry['name'])
                tb2 = '(' + str(entry['type']) + ')'
            n = n + 1
        tunera = ta1
        tunera1 = ta2
        tunerb = tb1
        tunerb1 = tb2
        self['key_tuner0'].setText('Tuner')
        self['key_tuner1'].setText(str(tunerb))
        self['key_tuner2'].setText(str(tunerb1))
        T = str(config.Nims[1].dvbt.terrestrial.value)
        self['key_T2'].setText(str(T))
        self['key_sat0'].setText('Tower')
        self['key_sat1'].setText('transmitter')
        self['key_sat2'].setText('DVB-T2')
    def OK(self):
        self.close()
class EvgQuickSignalBitrate(Screen):
    sz_w = getDesktop(0).size().width()
    if sz_w == 1920:
        skin = EQSSATBITRATE_HD
    def __init__(self, session, args=0):
        self.session = session
        Screen.__init__(self, session)
        self['avcur'] = Pixmap()
        self['aacur'] = Pixmap()
        self['vraz'] = StaticText(' ')
        self['araz'] = StaticText(' ')
        self.avcur = 0
        self.aacur = 0
        self.onShow.append(self.movePosition)
        self.startDelayTimer = eTimer()
        self.startDelayTimer.callback.append(self.bitrateAfrterDelayStart)
        self['vcur'] = StaticText()
        self['acur'] = StaticText()
        self['vmin'] = StaticText()
        self['amin'] = StaticText()
        self['vmax'] = StaticText()
        self['amax'] = StaticText()
        self['vavg'] = StaticText()
        self['aavg'] = StaticText()
        self.bitrate = Bitrate(session, self.refreshEvent, self.bitrateStopped)
        self.onLayoutFinish.append(self.__layoutFinished)
        self['actions'] = ActionMap(['OkCancelActions', 'DirectionActions', 'HelpActions', 'EPGSelectActions'], {'cancel': self.Exit}, (-1))
    def movePosition(self):
        self['avcur'].move(ePoint((-200), (-200)))
        self['avcur'].instance.setPixmapFromFile('/usr/lib/enigma2/python/Plugins/Extensions/EvgQuickSignal/images/down.png')
        self['avcur'].instance.show()
        self['aacur'].move(ePoint((-200), (-200)))
        self['aacur'].instance.setPixmapFromFile('/usr/lib/enigma2/python/Plugins/Extensions/EvgQuickSignal/images/up.png')
        self['aacur'].instance.show()
    def __layoutFinished(self):
        self.bitrateUpdateStart()
    def bitrateUpdateStart(self, delay=0):
        self.startDelayTimer.stop()
        self.startDelayTimer.start(delay, True)
    def bitrateAfrterDelayStart(self):
        if not self.bitrateUpdateStatus():
            self.bitrate.start()
    def bitrateUpdateStatus(self):
        return self.bitrate.running
    def bitrateUpdateStop(self):
        self.startDelayTimer.stop()
        if self.bitrateUpdateStatus():
            self.bitrate.stop()
    def refreshEvent(self):
        if int(self.bitrate.vcur) - self.avcur <= 0:
            self['avcur'].move(ePoint(570, 370))
            self['avcur'].instance.setPixmapFromFile('/usr/lib/enigma2/python/Plugins/Extensions/EvgQuickSignal/images/down.png')
            self['avcur'].instance.show()
            self['vraz'].setText('(' + str(int(self.bitrate.vcur) - self.avcur) + ')')
        if int(self.bitrate.vcur) - self.avcur > 0:
            self['avcur'].move(ePoint(570, 370))
            self['avcur'].instance.setPixmapFromFile('/usr/lib/enigma2/python/Plugins/Extensions/EvgQuickSignal/images/up.png')
            self['avcur'].instance.show()
            self['vraz'].setText('(+' + str(int(self.bitrate.vcur) - self.avcur) + ')')
        self['vcur'].setText(str(self.bitrate.vcur) + _(' kbit/s'))
        self.avcur = int(self.bitrate.vcur)
        if int(self.bitrate.acur) - self.aacur <= 0:
            self['aacur'].move(ePoint(570, 524))
            self['aacur'].instance.setPixmapFromFile('/usr/lib/enigma2/python/Plugins/Extensions/EvgQuickSignal/images/down.png')
            self['aacur'].instance.show()
            self['araz'].setText('(' + str(int(self.bitrate.acur) - self.aacur) + ')')
        if int(self.bitrate.acur) - self.aacur > 0:
            self['aacur'].move(ePoint(570, 524))
            self['aacur'].instance.setPixmapFromFile('/usr/lib/enigma2/python/Plugins/Extensions/EvgQuickSignal/images/up.png')
            self['aacur'].instance.show()
            self['araz'].setText('(+' + str(int(self.bitrate.acur) - self.aacur) + ')')
        self['acur'].setText(str(self.bitrate.acur) + _(' kbit/s'))
        self.aacur = int(self.bitrate.acur)
        self['vmin'].setText(str(self.bitrate.vmin) + _(' kbit/s'))
        self['amin'].setText(str(self.bitrate.amin) + _(' kbit/s'))
        self['vavg'].setText(str(self.bitrate.vavg) + _(' kbit/s'))
        self['aavg'].setText(str(self.bitrate.aavg) + _(' kbit/s'))
        self['vmax'].setText(str(self.bitrate.vmax) + _(' kbit/s'))
        self['amax'].setText(str(self.bitrate.amax) + _(' kbit/s'))
        self.avcur = int(self.bitrate.vcur)
    def bitrateStopped(self, retval):
        self.close()
    def Exit(self):
        self.bitrate.stop()
        self.close()
class EvgQuickSignalError(Screen):
    skin = EQSERROR_HD
    def __init__(self, session, args=0):
        self.session = session
        Screen.__init__(self, session)
        self['tears'] = Pixmap()
        self.tears = 0
        self.onstart()
        self['actions'] = ActionMap(['OkCancelActions', 'DirectionActions', 'HelpActions', 'EPGSelectActions'], {'cancel': self.Exit}, (-1))
        self.onShow.append(self.setPosition)
        Thread4 = Thread(target=self.tears1)
        Thread4.start()
    def setPosition(self):
        self['tears'].move(ePoint(50, 50))
        self['tears'].instance.setPixmapFromFile('/usr/lib/enigma2/python/Plugins/Extensions/EvgQuickSignal/tears/frame-1_1.png')
        self['tears'].instance.show()
    def tears1(self):
        self.moveTimer4 = eTimer()
        self.moveTimer4.callback.append(self.movePosition4)
        self.moveTimer4.start(500, 1)
    def movePosition4(self):
        self.moveTimer4.start(75, 1)
        self.tears = self.tears + 1
        if self.tears >= 49:
            self.tears = 1
        self['tears'].move(ePoint(50, 50))
        self['tears'].instance.setPixmapFromFile('/usr/lib/enigma2/python/Plugins/Extensions/EvgQuickSignal/tears/frame-' + str(self.tears) + '_1.png')
        self['tears'].instance.show()
    def onstart(self):
        z = 7
    def Exit(self):
        self.close()
def onstart1():
    if os.path.exists('/tmp/ref2.info') == True:
        try:
            with open('/tmp/ref2.info', 'r', errors='ignore') as file:
                contents = file.readlines()
                ref = str(contents[0])
            S = ref.rstrip()
            file.close()
        except:
            S = ' '
    else:
        S = ' '
    L = len(S)
    n1 = S.find('::')
    S1 = S[n1 + 2:]
    S2 = S[:n1]
    InfoFiles = []
    files = listdir('/etc/enigma2/')
    files.sort()
    for name in files:
        testname = name.lower()
        if testname.endswith('.tv'):
            InfoFiles.append(name)
    m = 0
    ref = ''
    buk = ''
    while m < len(InfoFiles):
        lfile = '/etc/enigma2/' + InfoFiles[m]
        if os.path.exists(lfile) == True:
            with open(lfile, 'r', errors='ignore') as f:
                count = sum((1 for _ in f))
            f = open(lfile, 'r', errors='ignore')
            data_lines = f.readlines()
            f.close()
            newstr = []
            for i in data_lines:
                newstr.append(i.rstrip())
            countstr = []
            n = 1
            while n < len(newstr):
                if S1 in newstr[n] and S2 in newstr[n]:
                        ref = newstr[n]
                        buk = lfile
                        countstr.append(newstr[n])
                        break
                n = n + 1
        m = m + 1
    if os.path.exists(buk) == True:
        try:
            with open(buk, 'r', errors='ignore') as file:
                contents = file.readlines()
                ref2 = str(contents[0])
            K = ref2.rstrip()
            file.close()
        except:
            K = ' '
    else:
        K = ' '
    bouquet = K.replace('#NAME ', '')
    ref3 = ref.replace('#SERVICE ', '')
    ref4 = ref3.replace('%3a', ':')
    url = ref4.replace(':' + S1, '')
    url1 = url.replace(S2 + ':', '')
    t1 = url1.find('@')
    D1 = url1[t1 + 1:]
    t2 = D1.find(':')
    port = D1[t2 + 1:]
    ipcam = D1[:t2]
    D2 = url1[:t1]
    t3 = D2.find('://')
    protocol = D2[:t3]
    D4 = D2[t3 + 3:]
    t4 = D4.find(':')
    login = D4[:t4]
    password = D4[t4 + 1:]
    ds = open('/tmp/ref3.info', 'w')
    ds.write(ref4)
    ds.write('\n')
    ds.write(bouquet)
    ds.write('\n')
    ds.write(S1)
    ds.write('\n')
    ds.write(S2)
    ds.write('\n')
    ds.write(url1)
    ds.write('\n')
    ds.write(port)
    ds.write('\n')
    ds.write(ipcam)
    ds.write('\n')
    ds.write(protocol)
    ds.write('\n')
    ds.write(login)
    ds.write('\n')
    ds.write(password)
    ds.write('\n')
    ds.close()
    if 'tcp' in ref4 and ':37777:' in ref4:
            return 1
    if 'udp' in ref4 and ':37778:' in ref4:
            return 1
    if 'http' in ref4 and ':80:' in ref4:
            return 1
    if 'rtmp' in ref4 and ':1935:' in ref4:
            return 1
    if 'https' in ref4 and ':443:' in ref4:
            return 1
    if 'rtsp' in ref4 and ':554:' in ref4:
            return 1
    return 2
def onstart0(session):
    service = session.nav.getCurrentService()
    info = service and service.info()
    tunertype = ' '
    if info is not None:
        feinfo = service and service.frontendInfo()
        if feinfo is not None:
            frontendData = feinfo and feinfo.getAll(True)
            if frontendData is not None:
                if frontendData.get('tuner_type') == 'DVB-S':
                    tunertype = frontendData.get('tuner_type')
                if frontendData.get('tuner_type') == 'DVB-T':
                    tunertype = frontendData.get('tuner_type')
    sz_w = getDesktop(0).size().width()
    if sz_w != 1920:
        session.open(EvgQuickSignalHDSkin)
    else:
        if tunertype == 'DVB-S':
            session.open(EvgQuickSignalSAT)
        else:
            if tunertype == 'DVB-T':
                session.open(EvgQuickSignalT2)
            else:
                service = session.nav.getCurrentService()
                if isinstance(service, iPlayableServicePtr):
                    info = service and service.info()
                    ref = None
                else:
                    info = service and source.info
                    ref = service
                if not info:
                    return ''
                else:
                    refname = 'ServiceName2.ref'
                    searchpath = ['/etc/enigma2/']
                    if ref:
                        refstr = ref.toString()
                        try:
                            s = open('/tmp/ref2.info', 'w')
                            s.write(str(refstr))
                            s.close()
                        except:
                            pass
                    else:
                        refstr = info.getInfoString(iServiceInformation.sServiceref)
                        try:
                            s = open('/tmp/ref2.info', 'w')
                            s.write(str(refstr))
                            s.close()
                        except:
                            pass
                    if refstr is None:
                        refstr = ''
                    if '%3a17999/' in str(refstr):
                        session.open(EvgQuickSignalError)
                    else:
                        if '%3a9999/' in str(refstr):
                            session.open(EvgQuickSignalT2MI)
                        else:
                            if refstr.startswith('1') == False:
                                if onstart1() == 1:
                                    session.open(EvgQuickSignalIPCAM)
                                if onstart1() == 2:
                                    session.open(EvgQuickSignalIPTV)
                            else:
                                session.open(EvgQuickSignalError)