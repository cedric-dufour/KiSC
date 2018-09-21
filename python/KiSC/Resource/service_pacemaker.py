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
import stat
import time


#------------------------------------------------------------------------------
# CLASSES
#------------------------------------------------------------------------------

class KiscResource_service_pacemaker(KiscResource):
    """
    Libvirt resource

    Configuration parameters are:
     - [REQUIRED] name (STRING):
       (Pacemaker) resource name
     - [OPTIONAL] resource_file (STRING; path):
       (Pacemaker) resource configuration file (*.xml)
       if specified, the (Pacemaker) resource configuration will be created/updated
       based on the given file when the resource is started
     - [OPTIONAL] constraint_file (STRING; path):
       (Pacemaker) constraint configuration file (*.xml)
       if specified, the (Pacemaker) constraint configuration will be created/updated
       based on the given file when the resource is started
     - [OPTIONAL] timeout_start (NUMBER; seconds[*15]):
       maximum time to wait for (Pacemaker) resource to start
     - [OPTIONAL] timeout_stop (NUMBER; seconds[*60]):
       maximum time to wait for (Pacemaker) resource to stop
     - [OPTIONAL] cleanup (*no|yes):
       whether to delete the (Pacemaker) resource/constraint configuration when
       the resource is stopped

    For further details, see:
     - [CLI] man cibadmin
     - [CLI] man crm_resource
    """


    #--------------------------------------------------------------------------
    # CONSTRUCTORS
    #--------------------------------------------------------------------------

    def __init__(self, _sId, _dsConfig):
        KiscResource.__init__(self, _sId, _dsConfig)

        # Properties
        self._bCacheInitialized = False
        self._sCachedResourceFile = None
        self._sCachedConstraintFile = None


    #--------------------------------------------------------------------------
    # METHODS: self
    #--------------------------------------------------------------------------

    def _cleanup(self):
        if KiscRuntime.parseBool(self._dsConfig.get('cleanup', False)):
            if 'constraint_file' in self._dsConfig:
                KiscRuntime.shell(['cibadmin', '-o', 'constraints', '-d', '-f', '-A', '//rsc_location[@rsc=\'%s\']' % self._dsConfig['name']], _bTrace = self._iVerbose >= KiscRuntime.VERBOSE_TRACE)
                time.sleep(3)
            if 'resource_file' in self._dsConfig:
                KiscRuntime.shell(['cibadmin', '-o', 'resources', '-D', '-A', '//primitive[@id=\'%s\'] | //group[@id=\'%s\']' % (self._dsConfig['name'], self._dsConfig['name'])], _bTrace = self._iVerbose >= KiscRuntime.VERBOSE_TRACE)
                time.sleep(3)


    #--------------------------------------------------------------------------
    # METHODS: KiscResource (implemented/overriden)
    #--------------------------------------------------------------------------

    def type(self):
        return 'service_pacemaker'


    def verify(self):
        lsErrors = list()
        if not len(self._dsConfig.get('name', str())):
            lsErrors.append('Invalid resource configuration; missing "name" parameter')
        return lsErrors


    def cache(self, _sDirectoryCache):
        lsCachedFiles = list()
        if 'resource_file' in self._dsConfig:
            self._sCachedResourceFile = _sDirectoryCache+os.sep+self.type()+'#'+self.id()+'.resource_file.xml'
            lsCachedFiles.append((self._dsConfig['resource_file'], self._sCachedResourceFile, (0, 0, stat.S_IRUSR|stat.S_IWUSR)))
        if 'constraint_file' in self._dsConfig:
            self._sCachedConstraintFile = _sDirectoryCache+os.sep+self.type()+'#'+self.id()+'.constraint_file.xml'
            lsCachedFiles.append((self._dsConfig['constraint_file'], self._sCachedConstraintFile, (0, 0, stat.S_IRUSR|stat.S_IWUSR)))
        return (list(), lsCachedFiles)


    def start(self):
        if self._iVerbose: self._INFO('Starting')
        lsErrors = list()

        # Be idempotent
        if self.status(True, KiscRuntime.STATUS_STARTED) == KiscRuntime.STATUS_STARTED:
            if self._iVerbose: self._INFO('Already started')
            return lsErrors

        # Start the resource
        try:

            # ... timeout
            try:
                iTimeout = int(self._dsConfig['timeout_start'])
            except KeyError:
                iTimeout = 15
            except ValueError:
                raise RuntimeError('Invalid timeout value (%s)' % self._dsConfig['timeout_start'])

            # ... check cache
            if self._sCachedResourceFile is None and 'resource_file' in self._dsConfig:
                raise RuntimeError('Resource configuration file not cached')
            if self._sCachedConstraintFile is None and 'constraint_file' in self._dsConfig:
                raise RuntimeError('Constraint configuration file not cached')

            # ... update Pacemaker resource/constraint configuration
            if self._sCachedResourceFile is not None:
                KiscRuntime.shell(['cibadmin', '-o', 'resources', '-M', '-c', '-x', self._sCachedResourceFile], _bTrace = self._iVerbose >= KiscRuntime.VERBOSE_TRACE)
                time.sleep(3)
            if self._sCachedConstraintFile is not None:
                KiscRuntime.shell(['cibadmin', '-o', 'constraints', '-M', '-c', '-x', self._sCachedConstraintFile], _bTrace = self._iVerbose >= KiscRuntime.VERBOSE_TRACE)
                time.sleep(3)

            # ... start resource
            KiscRuntime.shell(['crm_resource', '-Q', '-r', self._dsConfig['name'], '-m', '-p', 'target-role', '-v', 'Started'], _bTrace = self._iVerbose >= KiscRuntime.VERBOSE_TRACE)

            # ... wait for resource to start
            while iTimeout >= 0:
                iTimeout -= 1
                if KiscRuntime.shell(['crm_resource', '-Q', '-r', self._dsConfig['name'], '-W'], _bTrace = self._iVerbose >= KiscRuntime.VERBOSE_TRACE).strip():
                    break;
                if iTimeout < 0:
                    raise RuntimeError('Resource did not start')
                time.sleep(1)

            # ... done
            self._iStatus = KiscRuntime.STATUS_STARTED

        except (OSError, RuntimeError) as e:
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
            try:
                # ... clean-up configuration
                self._cleanup()
            except OSError as e:
                if self._iVerbose: self._ERROR(str(e))
                self._iStatus = KiscRuntime.STATUS_ERROR
                lsErrors.append(str(e))
            return lsErrors

        # Stop the resource
        try:

            # ... timeout
            try:
                iTimeout = int(self._dsConfig['timeout_stop'])
            except (KeyError, ValueError):
                iTimeout = 60

            # ... stop resource
            KiscRuntime.shell(['crm_resource', '-Q', '-r', self._dsConfig['name'], '-m', '-p', 'target-role', '-v', 'Stopped'], _bTrace = self._iVerbose >= KiscRuntime.VERBOSE_TRACE)

            # ... wait for resource to stop
            while iTimeout >= 0:
                iTimeout -= 1
                if not KiscRuntime.shell(['crm_resource', '-Q', '-r', self._dsConfig['name'], '-W'], _bTrace = self._iVerbose >= KiscRuntime.VERBOSE_TRACE).strip():
                    break;
                if iTimeout < 0:
                    raise RuntimeError('Resource did not stop')
                time.sleep(1)

            # ... clean-up configuration
            self._cleanup()

            # ... done
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

            # Locate resource on Pacekamer cluster
            try:
                sOutput = KiscRuntime.shell(['crm_resource', '-Q', '-r', self._dsConfig['name'], '-W'], _bTrace = self._iVerbose >= KiscRuntime.VERBOSE_TRACE).strip()
                if sOutput is None or not len(sOutput):
                    if '$PACEMAKER_NODES' in self._dsConfig:
                        del self._dsConfig['$PACEMAKER_NODES']
                    iStatus = KiscRuntime.STATUS_STOPPED
                else:
                    self._dsConfig['$PACEMAKER_NODES'] = sOutput
                    iStatus = KiscRuntime.STATUS_STARTED
            except OSError as e:
                if e.filename == 0 and e.errno == 6:
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
