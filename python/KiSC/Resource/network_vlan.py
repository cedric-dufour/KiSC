# -*- mode:python; tab-width:4; c-basic-offset:4; intent-tabs-mode:nil; -*-
# ex: filetype=python tabstop=4 softtabstop=4 shiftwidth=4 expandtab autoindent smartindent

# K.I.S.S. Cluster (KiSC)
# COPYRIGHT 2017-2018 Idiap Research Institute <http://www.idiap.ch>
#
# K.I.S.S. Cluster (KiSC) is free software:
# you can redistribute it and/or modify it under the terms of the GNU General
# Public License as published by the Free Software Foundation, Version 3.
#
# K.I.S.S. Cluster (KiSC) is distributed in the hope
# that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# See the GNU General Public License for more details.
#
# SPDX-License-Identifier: GPL-3.0
# License-Filename: LICENSE/GPL-3.0.txt
#
# AUTHORS:
# - Cédric Dufour <cedric.dufour@idiap.ch>


#------------------------------------------------------------------------------
# MODULES
#------------------------------------------------------------------------------

# KiSC
from KiSC.Runtime import KiscRuntime
from KiSC.Resource import KiscResource


#------------------------------------------------------------------------------
# CLASSES
#------------------------------------------------------------------------------

class KiscResource_network_vlan(KiscResource):
    """
    VLAN network resource

    Configuration parameters are:
     - [REQUIRED] name (STRING):
       VLAN name
     - [REQUIRED] vlan (0-4095):
       VLAN (numerical) ID
     - [REQUIRED] device (STRING):
       physical network device (interface) name

    (VLAN parameters)
     - [OPTIONAL] protocol (802.1Q|802.1ad):
       VLAN protocol
     - [OPTIONAL] reorder_hdr (on|off):
       packet header reordering
     - [OPTIONAL] gvrp (on|off):
       Generic VLAN Registration Protocol (GVRP)
     - [OPTIONAL] mvrp (on|off):
       Multiple VLAN Registration Protocol (MVRP)
     - [OPTIONAL] loose_binding (on|off):
       VLAN (device) state loose binding
     - [OPTIONAL] ingress_qos_map (comma-separated FROM:TO mappings):
       ingress QoS mapping
     - [OPTIONAL] egress_qos_map (comma-separated FROM:TO mappings):
       egress QoS mapping

    (device parameters)
     - [OPTIONAL] address (STRING; colon-separated hexadecimal MAC):
       link-layer (MAC) address
     - [OPTIONAL] mtu (NUMBER; bytes):
       Message Transmit Unit (MTU) lengh
     - [OPTIONAL] txqueuelen (NUMBER; packets):
       transmit queue length
     - [OPTIONAL] numtxqueues (NUMBER):
       quantity of tranmsit queues
     - [OPTIONAL] numrxqueues (NUMBER):
       quantity of receive queues

    For further details, see:
     - [CLI] man ip-link
     - [CLI] ip link add type vlan help
    """


    #--------------------------------------------------------------------------
    # CONSTRUCTORS
    #--------------------------------------------------------------------------

    def __init__(self, _sId, _dsConfig):
        KiscResource.__init__(self, _sId, _dsConfig)


    #--------------------------------------------------------------------------
    # METHODS: KiscResource (implemented/overriden)
    #--------------------------------------------------------------------------

    def type(self):
        return 'network_vlan'


    def verify(self):
        lsErrors = list()
        if not len(self._dsConfig.get('name', str())):
            lsErrors.append('Invalid resource configuration; missing "name" parameter')
        if not len(self._dsConfig.get('vlan', str())):
            lsErrors.append('Invalid resource configuration; missing "vlan" parameter')
        if not len(self._dsConfig.get('device', str())):
            lsErrors.append('Invalid resource configuration; missing "device" parameter')
        return lsErrors


    def start(self):
        if self._iVerbose: self._INFO('Starting')
        lsErrors = list()

        # Be idempotent
        if self.status(True, KiscRuntime.STATUS_STARTED) == KiscRuntime.STATUS_STARTED:
            if self._iVerbose: self._INFO('Already started')
            return lsErrors

        # Start the resource
        try:

            # ... add device
            lsCommand = [
                'ip', 'link', 'add',
                'link', self._dsConfig['device'],
                'name', self._dsConfig['name'],
            ]
            for sSetting in ['address', 'mtu', 'txqueuelen', 'numtxqueues', 'numrxqueues']:
                if sSetting in self._dsConfig:
                    lsCommand.extend([sSetting, self._dsConfig[sSetting]])
            lsCommand.extend(['type', 'vlan'])

            # ... protocol
            for sSetting in ['protocol']:
                if sSetting in self._dsConfig:
                    lsCommand.extend([sSetting, self._dsConfig[sSetting]])

            # ... VLAN ID
            lsCommand.extend(['id', self._dsConfig['vlan']])

            # ... options
            for sSetting in ['reorder_hdr', 'gvrp', 'mvrp', 'loose_binding']:
                if sSetting in self._dsConfig:
                    lsCommand.extend([sSetting, self._dsConfig[sSetting]])

            # ... QoS configuration
            for sSetting in ['ingress_qos_map', 'egress_qos_map']:
                if sSetting in self._dsConfig:
                    lsCommand.append(sSetting.replace('_', '-'))
                    for sMapping in self._dsConfig[sSetting].split(','):
                        lsCommand.append(sMapping)
            KiscRuntime.shell(lsCommand, _bTrace = self._iVerbose >= KiscRuntime.VERBOSE_TRACE)

            # ... UP!
            KiscRuntime.shell(['ip', 'link', 'set', self._dsConfig['name'], 'up'], _bTrace = self._iVerbose >= KiscRuntime.VERBOSE_TRACE)
            self._iStatus = KiscRuntime.STATUS_STARTED
            if self._iVerbose: self._INFO('Started')

        except OSError as e:
            if self._iVerbose: self._ERROR(str(e))
            self._iStatus = KiscRuntime.STATUS_ERROR
            lsErrors.append(str(e))

        # Done
        return lsErrors


    def stop(self):
        if self._iVerbose: self._INFO('Stopping')
        lsErrors = list()

        # Be idempotent
        if self.status(True, KiscRuntime.STATUS_STOPPED) == KiscRuntime.STATUS_STOPPED:
            if self._iVerbose: self._INFO('Already stopped')
            return lsErrors

        # Stop the resource

        # ... DOWN!
        try:
            KiscRuntime.shell(['ip', 'link', 'set', self._dsConfig['name'], 'down'], _bTrace = self._iVerbose >= KiscRuntime.VERBOSE_TRACE)
        except OSError as e:
            if self._iVerbose: self._WARNING(str(e))
            lsErrors.append(str(e))

        # ... delete device
        try:
            KiscRuntime.shell(['ip', 'link', 'delete', self._dsConfig['name']], _bTrace = self._iVerbose >= KiscRuntime.VERBOSE_TRACE)
            self._iStatus = KiscRuntime.STATUS_STOPPED
            if self._iVerbose: self._INFO('Stopped')
        except OSError as e:
            if self._iVerbose: self._ERROR(str(e))
            self._iStatus = KiscRuntime.STATUS_ERROR
            lsErrors.append(str(e))

        # Done
        return lsErrors


    def status(self, _bStateful = True, _iIntent = None):
        if self._iVerbose: self._INFO('Querying status')
        iStatus = KiscRuntime.STATUS_STARTED

        if _bStateful:

            # Exists ?
            # NOTE: look only for a name match, independently from potentially mismatching
            #       type, VLAN ID, physical device or options
            try:
                KiscRuntime.shell(['test', '-e', '/sys/class/net/%s' % self._dsConfig['name']], _bTrace = self._iVerbose >= KiscRuntime.VERBOSE_TRACE)
            except OSError as e:
                if e.filename == 0 and e.errno == 1:
                    iStatus = KiscRuntime.STATUS_STOPPED
                else:
                    if self._iVerbose: self._ERROR(str(e))
                    iStatus = KiscRuntime.STATUS_ERROR

            # UP ?
            if iStatus == KiscRuntime.STATUS_STARTED and _iIntent == KiscRuntime.STATUS_STARTED:
                try:
                    KiscRuntime.shell(['grep', '-Fq', 'up', '/sys/class/net/%s/operstate' % self._dsConfig['name']], _bTrace = self._iVerbose >= KiscRuntime.VERBOSE_TRACE)
                except OSError as e:
                    if self._iVerbose: self._ERROR(str(e))
                    iStatus = KiscRuntime.STATUS_ERROR

        else:
            iStatus = self._iStatus 

        # Done
        self._iStatus = iStatus
        if self._iVerbose: self._INFO('Status is %s' % KiscRuntime.STATUS_MESSAGE[self._iStatus])
        return self._iStatus
