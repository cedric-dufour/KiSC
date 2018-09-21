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


#------------------------------------------------------------------------------
# CLASSES
#------------------------------------------------------------------------------

class KiscResource_health_stonith(KiscResource):
    """
    STONITH device health check

    Configuration parameters are:
     - [REQUIRED] device_type (STRING):
       device type (e.g. 'external/ssh')
     - [OPTIONAL] parameters (STRING; comma-separated <name>=<value> pairs):
       device parameters (as per 'stonith -t <device_type> -n')
     - [OPTIONAL] count (NUMBER [*1]):
       number of times to perform the check

    For further details, see:
     - [CLI] man stonith
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
        return 'health_stonith'


    def verify(self):
        lsErrors = list()
        if not len(self._dsConfig.get('device_type', str())):
            lsErrors.append('Invalid resource configuration; missing "device_type" setting')
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

            # ... stonith command
            lsCommand = ['stonith', '-s', '-S', '-t', self._dsConfig['device_type']]

            # ... arguments
            lsCommand.extend(['-c', self._dsConfig.get('count', '1')])

            # ... parameters
            if 'parameters' in self._dsConfig:
                dsParameters = KiscRuntime.parseDictionary(self._dsConfig['parameters'], _sAssignmentOperator = '=')
                for sParameter_name in dsParameters:
                    lsCommand.append('%s=%s' % (sParameter_name, dsParameters[sParameter_name]))

            # ... do it !
            KiscRuntime.shell(lsCommand, _bTrace = self._iVerbose >= KiscRuntime.VERBOSE_TRACE)
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
