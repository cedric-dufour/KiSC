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

class KiscResource_service_dummy(KiscResource):
    """
    Dummy service (for test purposes)
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
        return 'service_dummy'


    def verify(self):
        return list()


    def start(self):
        self._iStatus = KiscRuntime.STATUS_STARTED
        if self._iVerbose: self._INFO('Started')
        return list()


    def suspend(self):
        self._iStatus = KiscRuntime.STATUS_SUSPENDED
        if self._iVerbose: self._INFO('Suspended')
        return list()


    def resume(self):
        self._iStatus = KiscRuntime.STATUS_STARTED
        if self._iVerbose: self._INFO('Resumed')
        return list()


    def stop(self):
        self._iStatus = KiscRuntime.STATUS_STOPPED
        if self._iVerbose: self._INFO('Stopped')
        return list()


    def status(self, _bStateful = True, _iIntent = None):
        if self._iStatus == KiscRuntime.STATUS_UNKNOWN:
            self._iStatus = KiscRuntime.STATUS_STOPPED
        if self._iVerbose: self._INFO('Status is %s' % KiscRuntime.STATUS_MESSAGE[self._iStatus])
        return self._iStatus
