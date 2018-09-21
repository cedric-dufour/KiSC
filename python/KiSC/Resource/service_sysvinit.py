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

# Standard
import os
import time


#------------------------------------------------------------------------------
# CLASSES
#------------------------------------------------------------------------------

class KiscResource_service_sysvinit(KiscResource):
    """
    System V init script

    Configuration parameters are:
     - [REQUIRED] name (STRING):
       init script name
     - [OPTIONAL] restart (*no|yes):
       restart unit if already started

    For further details, see:
     - [CLI] man invoke-rc.d
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
        return 'service_sysvinit'


    def verify(self):
        lsErrors = list()
        if not len(self._dsConfig.get('name', str())):
            lsErrors.append('Invalid resource configuration; missing "name" parameter')
        return lsErrors


    def start(self):
        if self._iVerbose: self._INFO('Starting')
        lsErrors = list()

        # Restart ?
        bRestart = KiscRuntime.parseBool(self._dsConfig.get('restart', False))

        # Be idempotent
        if self.status(True, KiscRuntime.STATUS_STARTED) == KiscRuntime.STATUS_STARTED:
            if not bRestart:
                if self._iVerbose: self._INFO('Already started')
                return lsErrors
            else:
                if self._iVerbose: self._INFO('Restarting')
        else:
            bRestart = False

        # Start the resource
        try:
            if bRestart:
                KiscRuntime.shell(['invoke-rc.d', '--quiet', self._dsConfig['name'], 'restart'], _bTrace = self._iVerbose >= KiscRuntime.VERBOSE_TRACE)
            else:
                KiscRuntime.shell(['invoke-rc.d', '--quiet', self._dsConfig['name'], 'start'], _bTrace = self._iVerbose >= KiscRuntime.VERBOSE_TRACE)
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
        try:
            KiscRuntime.shell(['invoke-rc.d', '--quiet', self._dsConfig['name'], 'stop'], _bTrace = self._iVerbose >= KiscRuntime.VERBOSE_TRACE)
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
        iStatus = KiscRuntime.STATUS_UNKNOWN

        if _bStateful:

            # Exists ?
            try:
                KiscRuntime.shell(['invoke-rc.d', '--quiet', self._dsConfig['name'], 'status'], _bTrace = self._iVerbose >= KiscRuntime.VERBOSE_TRACE)
                iStatus = KiscRuntime.STATUS_STARTED
            except OSError as e:
                # REF: http://refspecs.linuxbase.org/LSB_3.1.0/LSB-Core-generic/LSB-Core-generic/iniscrptact.html
                if e.filename == 0 and e.errno == 3:
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
