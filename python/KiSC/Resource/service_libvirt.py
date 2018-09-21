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

class KiscResource_service_libvirt(KiscResource):
    """
    Libvirt resource

    Configuration parameters are:
     - [REQUIRED] name (STRING):
       domain name
     - [OPTIONAL] config_file (STRING; path):
       domain configuration file (*.xml)
       if specified, the domain will be 'virsh create'd
       otherwise, it will be 'virsh start'ed (assuming it has been 'virsh define'd beforehands)
     - [OPTIONAL] remote_uri (STRING; URI[*qemu://%{host}/system]):
       remote host's URI (%{host} and %{hostname} variables shall be replaced with the actual host's ID or name)
     - [OPTIONAL] timeout_start (NUMBER; seconds[*5]):
       maximum time to wait for domain to start
     - [OPTIONAL] timeout_suspend (NUMBER; seconds[*5]):
       maximum time to wait for domain to suspend
     - [OPTIONAL] timeout_resume (NUMBER; seconds[*5]):
       maximum time to wait for domain to resume
     - [OPTIONAL] timeout_stop (NUMBER; seconds[*15]):
       maximum time to wait for domain to stop
     - [OPTIONAL] timeout_migrate (NUMBER; seconds[*60]):
       maximum time to wait for domain to migrate

    For further details, see:
     - [CLI] man virsh
    """


    #--------------------------------------------------------------------------
    # CONSTRUCTORS
    #--------------------------------------------------------------------------

    def __init__(self, _sId, _dsConfig):
        KiscResource.__init__(self, _sId, _dsConfig)

        # Properties
        self._sCachedConfigFile = None


    #--------------------------------------------------------------------------
    # METHODS: KiscResource (implemented/overriden)
    #--------------------------------------------------------------------------

    def type(self):
        return 'service_libvirt'


    def verify(self):
        lsErrors = list()
        if not len(self._dsConfig.get('name', str())):
            lsErrors.append('Invalid resource configuration; missing "name" parameter')
        return lsErrors


    def cache(self, _sDirectoryCache):
        lsCachedFiles = list()
        if 'config_file' in self._dsConfig:
            self._sCachedConfigFile = _sDirectoryCache+os.sep+self.type()+'#'+self.id()+'.config_file.xml'
            lsCachedFiles.append((self._dsConfig['config_file'], self._sCachedConfigFile, (0, 0, stat.S_IRUSR|stat.S_IWUSR)))
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
                iTimeout = int(self._dsConfig.get('timeout_start', 5))
            except ValueError:
                raise RuntimeError('Invalid timeout value (%s)' % self._dsConfig['timeout_start'])

            # ... check cache
            if self._sCachedConfigFile is None and 'config_file' in self._dsConfig:
                raise RuntimeError('Configuration file not cached')

            # ... start/create domain
            if 'config_file' not in self._dsConfig:
                KiscRuntime.shell(['virsh', '-q', 'start', self._dsConfig['name']], _bTrace = self._iVerbose >= KiscRuntime.VERBOSE_TRACE)
            else:
                KiscRuntime.shell(['virsh', '-q', 'create', self._sCachedConfigFile], _bTrace = self._iVerbose >= KiscRuntime.VERBOSE_TRACE)

            # ... wait for domain to start
            while iTimeout >= 0:
                iTimeout -= 1
                try:
                    if KiscRuntime.shell(['virsh', 'domstate', self._dsConfig['name']], _bTrace = self._iVerbose >= KiscRuntime.VERBOSE_TRACE).strip() == 'running':
                        break;
                except OSError as e:
                    if e.filename == 0:
                        pass
                    else:
                        raise e
                if iTimeout < 0:
                    KiscRuntime.shell(['virsh', '-q', 'destroy', self._dsConfig['name']], _bTrace = self._iVerbose >= KiscRuntime.VERBOSE_TRACE)
                    raise RuntimeError('Domain did not stop')
                time.sleep(1)

            # ... done
            self._iStatus = KiscRuntime.STATUS_STARTED
            if self._iVerbose: self._INFO('Started')

        except (OSError, RuntimeError) as e:
            if self._iVerbose: self._ERROR(str(e))
            self._iStatus = KiscRuntime.STATUS_ERROR
            lsErrors.append(str(e))

        # Done
        return lsErrors


    def suspend(self):
        if self._iVerbose: self._INFO('Suspending')
        lsErrors = list()

        # Be idempotent
        iStatus = self.status(True, KiscRuntime.STATUS_SUSPENDED)
        if iStatus == KiscRuntime.STATUS_SUSPENDED:
            if self._iVerbose: self._INFO('Already suspended')
            return lsErrors

        # Suspending the resource
        if iStatus != KiscRuntime.STATUS_STARTED:
            raise RuntimeError('Domain not started')
        try:

            # ... timeout
            try:
                iTimeout = int(self._dsConfig.get('timeout_suspend', 5))
            except ValueError:
                raise RuntimeError('Invalid timeout value (%s)' % self._dsConfig['timeout_suspend'])

            # ... suspend domain
            KiscRuntime.shell(['virsh', '-q', 'suspend', self._dsConfig['name']], _bTrace = self._iVerbose >= KiscRuntime.VERBOSE_TRACE)

            # ... wait for domain to suspend
            while iTimeout >= 0:
                iTimeout -= 1
                try:
                    if KiscRuntime.shell(['virsh', 'domstate', self._dsConfig['name']], _bTrace = self._iVerbose >= KiscRuntime.VERBOSE_TRACE).strip() == 'paused':
                        break;
                except OSError as e:
                    if e.filename == 0:
                        break
                    else:
                        raise e
                if iTimeout < 0:
                    raise RuntimeError('Domain did not suspend')
                time.sleep(1)

            # ... done
            self._iStatus = KiscRuntime.STATUS_SUSPENDED
            if self._iVerbose: self._INFO('Suspended')

        except OSError as e:
            if self._iVerbose: self._ERROR(str(e))
            self._iStatus = KiscRuntime.STATUS_ERROR
            lsErrors.append(str(e))

        # Done
        return lsErrors


    def resume(self):
        if self._iVerbose: self._INFO('Resuming')
        lsErrors = list()

        # Be idempotent
        iStatus = self.status(True, KiscRuntime.STATUS_STARTED)
        if iStatus == KiscRuntime.STATUS_STARTED:
            if self._iVerbose: self._INFO('Domain is running')
            return lsErrors

        # Resuming the resource
        if iStatus != KiscRuntime.STATUS_SUSPENDED:
            raise RuntimeError('Domain not suspended')
        try:

            # ... timeout
            try:
                iTimeout = int(self._dsConfig.get('timeout_resume', 5))
            except ValueError:
                raise RuntimeError('Invalid timeout value (%s)' % self._dsConfig['timeout_resume'])

            # ... resume domain
            KiscRuntime.shell(['virsh', '-q', 'resume', self._dsConfig['name']], _bTrace = self._iVerbose >= KiscRuntime.VERBOSE_TRACE)

            # ... wait for domain to resume
            while iTimeout >= 0:
                iTimeout -= 1
                try:
                    if KiscRuntime.shell(['virsh', 'domstate', self._dsConfig['name']], _bTrace = self._iVerbose >= KiscRuntime.VERBOSE_TRACE).strip() == 'running':
                        break;
                except OSError as e:
                    if e.filename == 0:
                        break
                    else:
                        raise e
                if iTimeout < 0:
                    raise RuntimeError('Domain did not resume')
                time.sleep(1)

            # ... done
            self._iStatus = KiscRuntime.STATUS_RESUMED
            if self._iVerbose: self._INFO('Resumed')

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

            # ... timeout
            try:
                iTimeout = int(self._dsConfig.get('timeout_stop', 15))
            except ValueError:
                raise RuntimeError('Invalid timeout value (%s)' % self._dsConfig['timeout_stop'])

            # ... stop domain
            KiscRuntime.shell(['virsh', '-q', 'shutdown', self._dsConfig['name']], _bTrace = self._iVerbose >= KiscRuntime.VERBOSE_TRACE)

            # ... wait for domain to stop
            while iTimeout >= 0:
                iTimeout -= 1
                try:
                    if KiscRuntime.shell(['virsh', 'domstate', self._dsConfig['name']], _bTrace = self._iVerbose >= KiscRuntime.VERBOSE_TRACE).strip() == 'shut off':
                        break;
                except OSError as e:
                    if e.filename == 0:
                        break
                    else:
                        raise e
                if iTimeout < 0:
                    KiscRuntime.shell(['virsh', '-q', 'destroy', self._dsConfig['name']], _bTrace = self._iVerbose >= KiscRuntime.VERBOSE_TRACE)
                    raise RuntimeError('Domain did not stop')
                time.sleep(1)

            # ... done
            self._iStatus = KiscRuntime.STATUS_STOPPED
            if self._iVerbose: self._INFO('Stopped')

        except OSError as e:
            if self._iVerbose: self._ERROR(str(e))
            self._iStatus = KiscRuntime.STATUS_ERROR
            lsErrors.append(str(e))

        # Done
        return lsErrors


    def migrate(self, _oHost):
        if self._iVerbose: self._INFO('Migrating')
        lsErrors = list()

        # Be idempotent
        if self.status(True, KiscRuntime.STATUS_STARTED) != KiscRuntime.STATUS_STARTED:
            if self._iVerbose: self._INFO('Not started')
            return lsErrors

        # Migrate the resource
        try:

            # ... remote URI
            sRemoteUri = self._dsConfig.get('remote_uri', 'qemu://%{host}/system')
            sRemoteUri = sRemoteUri.replace('%{host}', _oHost.id())
            sRemoteUri = sRemoteUri.replace('%{hostname}', _oHost.getHostname())

            # ... timeout
            try:
                iTimeout = int(self._dsConfig.get('timeout_migrate', 60))
            except ValueError:
                raise RuntimeError('Invalid timeout value (%s)' % self._dsConfig['timeout_migrate'])

            # ... migrate domain
            lsCommand = ['virsh', '-q', 'migrate', '--live']
            if iTimeout > 0: lsCommand.extend(['--timeout', str(iTimeout), '--timeout-suspend'])
            lsCommand.extend([self._dsConfig['name'], sRemoteUri])
            KiscRuntime.shell(lsCommand, _bTrace = self._iVerbose >= KiscRuntime.VERBOSE_TRACE)

            # ... done
            self._iStatus = KiscRuntime.STATUS_STARTED
            if self._iVerbose: self._INFO('Started')

        except (OSError, RuntimeError) as e:
            if self._iVerbose: self._ERROR(str(e))
            self.status(True, KiscRuntime.STATUS_SUSPENDED)
            lsErrors.append(str(e))

        # Done
        return lsErrors


    def status(self, _bStateful = True, _iIntent = None):
        if self._iVerbose: self._INFO('Querying status')
        iStatus = KiscRuntime.STATUS_UNKNOWN

        if _bStateful:

            # Query domain state
            try:
                sOutput = KiscRuntime.shell(['virsh', 'domstate', self._dsConfig['name']], _bTrace = self._iVerbose >= KiscRuntime.VERBOSE_TRACE).strip()
                if sOutput is None or not len(sOutput):
                    iStatus = KiscRuntime.STATUS_ERROR
                elif sOutput == 'shut off':
                    iStatus = KiscRuntime.STATUS_STOPPED
                elif sOutput == 'paused':
                    iStatus = KiscRuntime.STATUS_SUSPENDED
                else:
                    iStatus = KiscRuntime.STATUS_STARTED
            except OSError as e:
                if e.filename == 0:
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
