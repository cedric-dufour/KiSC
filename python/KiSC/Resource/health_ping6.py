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
from KiSC.Resource import KiscResource
from KiSC.Runtime import KiscRuntime

# Standard
import copy


#------------------------------------------------------------------------------
# CLASSES
#------------------------------------------------------------------------------

class KiscResource_health_ping6(KiscResource):
    """
    (IPv6) Ping health check

    Configuration parameters are:
     - [REQUIRED] address (STRING; comma-separated, colon-separated hexadecimal IPv6):
       IPv6 network address(es) to ping
     - [OPTIONAL] satisfy (NUMBER):
       consider check successfull if the given count of addresses are reachable (default: all)
     - [OPTIONAL] count (NUMBER [*1]):
       ping packet(s) to send
     - [OPTIONAL] interval (NUMBER; seconds [*1]):
       interval between ping packet(s)
     - [OPTIONAL] timeout (NUMBER; seconds [*5]):
       individual timeout for each ping packet
     - [OPTIONAL] deadline (NUMBER; seconds):
       absolute deadline for (all) ping packet(s)
     - [OPTIONAL] interface (STRING):
       interface or IPv6 network address to send the ping packet(s) from
     - [OPTIONAL] mark (STRING):
       mark to tag ping packet(s) with
     - [OPTIONAL] flow (STRING):
       IPv6 flow label (hexadecimal) identifier

    For further details, see:
     - [CLI] man ping6
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
        return 'health_ping6'


    def verify(self):
        lsErrors = list()
        if not len(self._dsConfig.get('address', str())):
            lsErrors.append('Invalid resource configuration; missing "address" setting')
        return lsErrors


    def start(self):
        lsErrors = list()

        # Be idempotent
        if self.status(True, KiscRuntime.STATUS_STARTED) == KiscRuntime.STATUS_STARTED:
            if self._iVerbose: self._INFO('Already started')
            return lsErrors

        # Start the resource
        if self._iVerbose: self._INFO('Starting')
        try:

            # ... satisfy ?
            try:
                iSatisfy = int(self._dsConfig['satisfy'])
            except KeyError:
                iSatisfy = None
            except ValueError:
                raise RuntimeError('Invalid "satisfy" setting (%s)' % self._dsConfig['satisfy'])
            iSatisfied = 0

            # ... ping command
            lsCommand = ['ping6', '-q', '-n']

            # ... arguments
            lsCommand.extend(['-c', self._dsConfig.get('count', '1')])
            lsCommand.extend(['-i', self._dsConfig.get('interval', '1')])
            lsCommand.extend(['-W', self._dsConfig.get('timeout', '5')])

            # ... options
            if 'deadline' in self._dsConfig:
                lsCommand.extend(['-w', self._dsConfig['deadline']])
            if 'interface' in self._dsConfig:
                lsCommand.extend(['-I', self._dsConfig['interface']])
            if 'mark' in self._dsConfig:
                lsCommand.extend(['-m', self._dsConfig['mark']])
            if 'flow' in self._dsConfig:
                lsCommand.extend(['-F', self._dsConfig['flow']])

            # ... loop through IP address(es)
            iAddresses = 0
            for sAddress in self._dsConfig['address'].split(','):
                sAddress = sAddress.strip()
                if not len(sAddress): continue
                iAddresses += 1
                lsCommand_sub = copy.deepcopy(lsCommand)
                lsCommand_sub.append(sAddress)
                try:
                    KiscRuntime.shell(lsCommand_sub, _bTrace = self._iVerbose >= KiscRuntime.VERBOSE_TRACE)
                    iSatisfied += 1
                except OSError as e:
                    if e.filename == 0 and e.errno == 1:
                        # address not reachable
                        pass
                    else:
                        raise e

            # ... satisfied ?
            if iSatisfy is None:
                if iSatisfied < iAddresses:
                    raise RuntimeError('Ping failed (%d<%d)' % (iSatisfied, iAddresses))
            else:
                if iSatisfied < iSatisfy:
                    raise RuntimeError('Ping failed (%d<%d)' % (iSatisfied, iSatisfy))
            self._iStatus = KiscRuntime.STATUS_STARTED
            if self._iVerbose: self._INFO('Started')

        except (OSError, RuntimeError) as e:
            if self._iVerbose: self._ERROR(str(e))
            self._iStatus = KiscRuntime.STATUS_ERROR
            lsErrors.append(str(e))

        # Done
        return lsErrors


    def stop(self):
        self._iStatus = KiscRuntime.STATUS_STOPPED
        if self._iVerbose: self._INFO('Stopped')
        return list()


    def status(self, _bStateful = True, _iIntent = None):
        if self._iVerbose: self._INFO('Status is %s' % KiscRuntime.STATUS_MESSAGE[self._iStatus])
        return self._iStatus
