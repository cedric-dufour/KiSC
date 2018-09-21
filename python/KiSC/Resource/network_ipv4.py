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

class KiscResource_network_ipv4(KiscResource):
    """
    IPv4 network resource

    Configuration parameters are:
     - [REQUIRED] address (STRING; dotted decimal IPv4):
       IPv4 network address
     - [REQUIRED] mask (NUMBER; CIDR):
       network mask/prefix length
     - [REQUIRED] device (STRING):
       network device (interface) name
     - [OPTIONAL] broadcast (STRING; dotted decimal IPv4):
       network broadcast address
     - [OPTIONAL] anycast (STRING; dotted decimal IPv4):
       network anycast address
     - [OPTIONAL] label (STRING):
       address label
     - [OPTIONAL] scope (*global|link|host|NUMBER):
       address scope

    For further details, see:
     - [CLI] man ip-address
     - [CLI] ip address help
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
        return 'network_ipv4'


    def verify(self):
        lsErrors = list()
        if not len(self._dsConfig.get('address', str())):
            lsErrors.append('Invalid resource configuration; missing "address" parameter')
        if not len(self._dsConfig.get('mask', str())):
            lsErrors.append('Invalid resource configuration; missing "mask" parameter')
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

            # ... add address
            lsCommand = [
                'ip', '-4', 'address', 'add',
                '%s/%s' % (self._dsConfig['address'], self._dsConfig['mask'])
            ]

            # ... options
            for sSetting in ['broadcast', 'anycast', 'label', 'scope']:
                if sSetting in self._dsConfig:
                    lsCommand.extend([sSetting, self._dsConfig[sSetting]])
            lsCommand.extend(['dev', self._dsConfig['device']])

            # ... DO IT!
            KiscRuntime.shell(lsCommand, _bTrace = self._iVerbose >= KiscRuntime.VERBOSE_TRACE)
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

        # ... delete address
        try:
            KiscRuntime.shell([
                'ip', '-4', 'address', 'delete',
                '%s/%s' % (self._dsConfig['address'], self._dsConfig['mask']),
                'dev', self._dsConfig['device']
            ], _bTrace = self._iVerbose >= KiscRuntime.VERBOSE_TRACE)
            self._iStatus = KiscRuntime.STATUS_STARTED
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
            # NOTE: look only for an address match, independently from potentially mismatching
            #       network mask, device or options
            try:
                KiscRuntime.shell([
                    [ 'ip', '-4', 'address', 'show' ],
                    [ 'grep', '-Fq', 'inet %s/' % self._dsConfig['address'] ]
                ], _bTrace = self._iVerbose >= KiscRuntime.VERBOSE_TRACE)
            except OSError as e:
                if e.filename == 0 and e.errno == 1:
                    iStatus = KiscRuntime.STATUS_STOPPED
                else:
                    if self._iVerbose: self._ERROR(str(e))
                    iStatus = KiscRuntime.STATUS_ERROR

        else:
            iStatus = self._iStatus 

        # Done
        self._iStatus = iStatus
        if self._iVerbose: self._INFO('Status is %s' % KiscRuntime.STATUS_MESSAGE[self._iStatus])
        return self._iStatus
