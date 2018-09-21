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


#------------------------------------------------------------------------------
# CLASSES
#------------------------------------------------------------------------------

class KiscResource_storage_mount(KiscResource):
    """
    Mounted storage resource

    Configuration parameters are:
     - [REQUIRED] fstype (STRING):
       filesytem type
     - [REQUIRED] device (STRING; path or URI):
       device path or resource URI to mount
     - [REQUIRED] mountpoint (STRING; path):
       mountpoint directory path
     - [OPTIONAL] options (STRING; comma-separated):
       mount options
     - [OPTIONAL] mkdir (*yes|no):
       create mountpoint directory, if needs be

    For further details, see:
     - [CLI] man mount
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
        return 'storage_mount'


    def verify(self):
        lsErrors = list()
        if not len(self._dsConfig.get('fstype', str())):
            lsErrors.append('Invalid resource configuration; missing "fstype" parameter')
        if not len(self._dsConfig.get('device', str())):
            lsErrors.append('Invalid resource configuration; missing "device" parameter')
        if not len(self._dsConfig.get('mountpoint', str())):
            lsErrors.append('Invalid resource configuration; missing "mountpoint" parameter')
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

            # ... mkdir ?
            if KiscRuntime.parseBool(self._dsConfig.get('mkdir', True)):
                os.makedirs(self._dsConfig['mountpoint'], exist_ok=True)

            # ... mount device
            lsCommand = ['mount', '-t', self._dsConfig['fstype']]
            if 'options' in self._dsConfig:
                lsCommand.extend(['-o', self._dsConfig['options']])
            lsCommand.extend([self._dsConfig['device'], self._dsConfig['mountpoint']])
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

        # ... unmount device
        try:
            KiscRuntime.shell(['umount', self._dsConfig['mountpoint']], _bTrace = self._iVerbose >= KiscRuntime.VERBOSE_TRACE)
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
            # NOTE: look only for a mountpoint match, independently from potentially mismatching
            #       fstype, device or options
            try:
                KiscRuntime.shell(['awk', 'BEGIN{e=22}; {if($2=="%s") {e=0; exit}}; END {exit e}' % self._dsConfig['mountpoint'], '/proc/mounts'], _bTrace = self._iVerbose >= KiscRuntime.VERBOSE_TRACE)
            except OSError as e:
                if e.filename == 0 and e.errno == 22:
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
