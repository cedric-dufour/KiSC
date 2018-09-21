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

class KiscResource_network_bond(KiscResource):
    """
    Network bond (trunk) resource

    Configuration parameters are:
     - [REQUIRED] name (STRING):
       bond name
     - [REQUIRED] mode (balance-rr|active-backup|balance-xor|broadcast|802.3ad|balance-tlb|balance-alb):
       bonding mode
     - [REQUIRED] devices (STRING; comma-separated):
       bonded network devices (interfaces) names -> links/slaves

    (bond parameters)
     - [OPTIONAL] miimon (NUMBER; milliseconds[*0]):
       links MII monitoring interval
     - [OPTIONAL] updelay (NUMBER; milliseconds[*0]):
       time to wait before enabling a slave after a link recovery
     - [OPTIONAL] downdelay (NUMBER; milliseconds[*0]):
       time to wait before disabling a slave after a link failure
     - [OPTIONAL] use_carrier (0|*1):
       use the link's driver carrier state for MII monitoring
     - [OPTIONAL] arp_interval (NUMBER; milliseconds[*0]):
       links ARP monitoring interval
     - [OPTIONAL] arp_ip_target (STRING; comma-separated dotted decimal IPv4):
       IPv4 addresses to use for ARP monitoring
     - [OPTIONAL] arp_all_targets (*any|all):
       which arp_ip_target to use for ARP monitoring [mode:active-backup]
     - [OPTIONAL] arp_validate (*none|active|backup|all|filter|filter_active|filter_backup):
       ARP monitoring validation policy
     - [OPTIONAL] primary (name):
       primary link/slave's device name
     - [OPTIONAL] primary_reselect (*always|better|failure):
       primary re-selection policy after primary link recovery
     - [OPTIONAL] active_slave (name):
       active link/slave's device name [mode:active-backup,balance-tlb,balance-alb]
     - [OPTIONAL] all_slaves_active (*0|1):
       when all slaves are active, duplicate frames will NOT be dropped
     - [OPTIONAL] fail_over_mac (*none|active|follow):
       bond/slaves MAC address attribution policy [mode:active-backup]
     - [OPTIONAL] xmit_hash_policy (*layer2|layer2+3|layer3+4):
       transmit hash policy [mode:balance-xor,802.3ad,balance-tlb]
     - [OPTIONAL] packets_per_slave (0-65535[*1]):
       number of packets to transmit per slave [mode:balance-rr]
     - [OPTIONAL] tlb_dynamic_lb (0|*1):
       dynamic shuffling of transmit flows [mode:balance-tlb]
     - [OPTIONAL] lacp_rate (*slow|fast):
       LACP rate [mode:802.3ad]
     - [OPTIONAL] ad_select (*stable|bandwidth|count):
       LACP aggregation selection policy [mode:802.3ad]
     - [OPTIONAL] num_grat_arp (0-255[*1]):
       number of gratuitous ARP packets to send after failover [mode:active-backup]
     - [OPTIONAL] num_unsol_na (0-255[*1]):
       number of unsollicited neighbor advertisement packets to send after failover [mode:active-backup]
     - [OPTIONAL] lp_interval (seconds[*1]):
       (sent) learning packets interval [mode:balance-tlb,balance-alb]
     - [OPTIONAL] resend_igmp (0-255[*0]):
       number of IGMP membership reports to send after failover [mode:balance-rr,balance-tlb,balance-alb]

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
     - [CLI] ip link add type bond help
     - [URL] https://www.kernel.org/doc/Documentation/networking/bonding.txt
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
        return 'network_bond'


    def verify(self):
        lsErrors = list()
        if not len(self._dsConfig.get('name', str())):
            lsErrors.append('Invalid resource configuration; missing "name" parameter')
        if not len(self._dsConfig.get('mode', str())):
            lsErrors.append('Invalid resource configuration; missing "mode" parameter')
        if not len(self._dsConfig.get('devices', str())):
            lsErrors.append('Invalid resource configuration; missing "devices" parameter')
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

            # ... load bonding driver (but do not create any default device)
            KiscRuntime.shell(['modprobe', 'bonding', 'max_bonds=0'], _bTrace = self._iVerbose >= KiscRuntime.VERBOSE_TRACE)

            # ... add device
            lsCommand = [
                'ip', 'link', 'add',
                'name', self._dsConfig['name'],
            ]
            for sSetting in ['address', 'mtu', 'txqueuelen', 'numtxqueues', 'numrxqueues']:
                if sSetting in self._dsConfig:
                    lsCommand.extend([sSetting, self._dsConfig[sSetting]])
            lsCommand.extend(['type', 'bond', 'mode', self._dsConfig['mode']])
            KiscRuntime.shell(lsCommand, _bTrace = self._iVerbose >= KiscRuntime.VERBOSE_TRACE)

            # ... options
            for sSetting in ['miimon', 'updelay', 'downdelay', 'use_carrier',
                             'arp_interval', 'arp_ip_target', 'arp_all_targets', 'arp_validate',
                             'primary_reselect',
                             'all_slaves_active', 'fail_over_mac', 'xmit_hash_policy', 'packets_per_slave', 'tlb_dynamic_lb',
                             'lacp_rate', 'ad_select',
                             'num_grat_arp', 'num_unsol_na', 'lp_interval', 'resend_igmp']:
                if sSetting in self._dsConfig:
                    KiscRuntime.echo(self._dsConfig[sSetting], '/sys/class/net/%s/bonding/%s' % (self._dsConfig['name'], sSetting), _bTrace = self._iVerbose >= KiscRuntime.VERBOSE_TRACE)

            # ... attach slaves
            for sDevice in self._dsConfig['devices'].split(','):
                KiscRuntime.shell(['ip', 'link', 'set', sDevice, 'master', self._dsConfig['name'], 'up'], _bTrace = self._iVerbose >= KiscRuntime.VERBOSE_TRACE)

            # ... default/active slave
            for sSetting in ['active_slave', 'primary']:
                if sSetting in self._dsConfig:
                    KiscRuntime.echo(self._dsConfig[sSetting], '/sys/class/net/%s/bonding/%s' % (self._dsConfig['name'], sSetting), _bTrace = self._iVerbose >= KiscRuntime.VERBOSE_TRACE)

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

        # ... detach slaves
        for sDevice in self._dsConfig['devices'].split(','):
            try:
                KiscRuntime.shell(['ip', 'link', 'set', sDevice, 'nomaster', 'down'], _bTrace = self._iVerbose >= KiscRuntime.VERBOSE_TRACE)
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
            #       type, devices, mode or options
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
