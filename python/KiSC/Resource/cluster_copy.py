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
import os
import os.path


#------------------------------------------------------------------------------
# CLASSES
#------------------------------------------------------------------------------

class KiscResource_cluster_copy(KiscResource):
    """
    Copy the given file (optionally performing cluster variables substitution)

    Configuration parameters are:
     - [REQUIRED] source (STRING; path):
       source file
     - [REQUIRED] destination (STRING; path):
       destination file
     - [OPTIONAL] mkdir (*yes|no):
       create destination directory, if needs be
     - [OPTIONAL] user (STRING|NUMBER):
       destination file owner user name or UID
     - [OPTIONAL] group (STRING|NUMBER):
       destination file owner group name or GID
     - [OPTIONAL] mode (NUMBER):
       destination file mode (octal mode bits)
     - [OPTIONAL] command_pre (STRING):
       command to execute before the file is cached
     - [OPTIONAL] command_post (STRING):
       command to execute after the file is cached
     - [OPTIONAL] config_file (STRING; path):
       cluster variables configuration file
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
        return 'cluster_copy'


    def verify(self):
        lsErrors = list()
        if not len(self._dsConfig.get('source', str())):
            lsErrors.append('Invalid resource configuration; missing "source" setting')
        if not len(self._dsConfig.get('destination', str())):
            lsErrors.append('Invalid resource configuration; missing "destination" setting')
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
                os.makedirs(os.path.dirname(self._dsConfig['destination']), exist_ok=True)

            # ... pre-cache command ?
            if 'command_pre' in self._dsConfig:
                KiscRuntime.shell(self._dsConfig['command_pre'].split(' '), _bTrace = self._iVerbose >= KiscRuntime.VERBOSE_TRACE)

            # ... permissions
            mUser = self._dsConfig.get('user', None)
            mGroup = self._dsConfig.get('group', None)
            try:
                mMode = int(self._dsConfig['mode'], 8)
            except KeyError:
                mMode = None

            # ... cache file
            if 'config_file' in self._dsConfig:
                oClusterConfig = KiscCluster_config(self._dsConfig['config_file'])
                sHost_id = oClusterConfig.getHostByHostname().id()
                oClusterConfig.resolveFile(self._dsConfig['source'], self._dsConfig['destination'], _sHost_id = sHost_id, _tPermissions = (mUser, mGroup, mMode))
            else:
                if self._iVerbose: self._DEBUG('Reading file (%s)' % self._dsConfig['source'])
                with open(self._dsConfig['source'], 'r') as oFile:
                    sFile = oFile.read()
                if self._iVerbose: self._DEBUG('Writing file (%s)' % self._dsConfig['destination'])
                iUmask = os.umask(0o077)
                oFile = None
                try:
                    oFile = open(self._dsConfig['destination'], 'w')
                    KiscRuntime.perms(oFile.fileno(), mUser, mGroup, mMode, _bTrace = self._iVerbose >= KiscRuntime.VERBOSE_TRACE)
                    oFile.write(sFile)
                finally:
                    if oFile: oFile.close()
                    os.umask(iUmask)

            # ... post-cache command ?
            if 'command_post' in self._dsConfig:
                KiscRuntime.shell(self._dsConfig['command_post'].split(' '), _bTrace = self._iVerbose >= KiscRuntime.VERBOSE_TRACE)

            # ... done
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
