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
from KiSC.Resource import \
     KiscResource, \
     kiscResource
from KiSC.Runtime import \
     KiscRuntime

# Standard
from configparser import \
     RawConfigParser
import os
import os.path
import stat
import sys


#------------------------------------------------------------------------------
# CLASSES
#------------------------------------------------------------------------------

class KiscCluster_resource:
    """
    Cluster-level resource object
    """

    #--------------------------------------------------------------------------
    # CONSTRUCTORS
    #--------------------------------------------------------------------------

    def __init__(self, _oClusterConfig, _sHost_id, _sResource_id, _bBootstrap = False):
        # Properties
        self._oClusterConfig = _oClusterConfig
        self._sHost_id = _sHost_id
        self._sResource_id = _sResource_id
        self._bBootstrap = _bBootstrap
        self._oResource = self._oClusterConfig.getResource(self._sResource_id, self._bBootstrap)

        # ... paths
        if self._bBootstrap:
            sResource_runtime_dir = self._oClusterConfig.getDirectoryRuntimeLocal()
        else:
            sResource_runtime_dir = self._oClusterConfig.getDirectoryRuntimeGlobal()
        sResource_resource_prefix = self._oResource.type()+':'+self._sResource_id
        sResource_runtime_file = sResource_runtime_dir+os.sep+sResource_resource_prefix+'.run'
        self._dsPaths = {
            'runtime_dir': sResource_runtime_dir,
            'resource_prefix': sResource_resource_prefix,
            'runtime_file': sResource_runtime_file,
        }

        # ... debugging
        self._iVerbose = KiscRuntime.VERBOSE_NONE


    #--------------------------------------------------------------------------
    # METHODS: self
    #--------------------------------------------------------------------------

    #
    # Debugging
    #

    def VERBOSE(self, _iVerbose):
        """
        Set verbosity level

        @param int _iVerbose  Verbosity level (self KiscRuntime.VERBOSE_* constants)
        """

        self._iVerbose = _iVerbose
        self._oResource.VERBOSE(self._iVerbose)


    def _ERROR(self, _sMessage):
        """
        Print ERROR message to standard error

        @param str _sMessage  Message to print
        """

        if(self._iVerbose >= KiscRuntime.VERBOSE_ERROR):
            sys.stderr.write('ERROR[CR:%s@%s] %s\n' % (self._sResource_id, self._sHost_id, _sMessage.replace('\n', '¬')))


    def _WARNING(self, _sMessage):
        """
        Print WARNING message to standard error

        @param str _sMessage  Message to print
        """

        if(self._iVerbose >= KiscRuntime.VERBOSE_WARNING):
            sys.stderr.write('WARNING[CR:%s@%s] %s\n' % (self._sResource_id, self._sHost_id, _sMessage.replace('\n', '¬')))


    def _INFO(self, _sMessage):
        """
        Print INFO message to standard error

        @param str _sMessage  Message to print
        """

        if(self._iVerbose >= KiscRuntime.VERBOSE_INFO):
            sys.stderr.write('INFO[CR:%s@%s] %s\n' % (self._sResource_id, self._sHost_id, _sMessage.replace('\n', '¬')))


    def _DEBUG(self, _sMessage):
        """
        Print DEBUG message to standard error

        @param str _sMessage  Message to print
        """

        if(self._iVerbose >= KiscRuntime.VERBOSE_DEBUG):
            sys.stderr.write('DEBUG[CR:%s@%s] %s\n' % (self._sResource_id, self._sHost_id, _sMessage.replace('\n', '¬')))

    #
    # Helpers
    #

    def resource(self):
        """
        Return the resource (object)

        @return KiscResource  Resource object
        """

        return self._oResource


    def existsRuntime(self):
        """
        Return whether the resource runtime configuration and status file exists

        @return bool  True is file exists, False otherwis

        @exception OSError  Runtime file I/O error
        """

        return os.path.isfile(self._dsPaths['runtime_file'])


    def saveRuntime(self):
        """
        Save the resource runtime configuration and status to file

        @exception OSError  Runtime file I/O error
        """
        if self._iVerbose: self._DEBUG('Saving runtime')

        os.makedirs(os.path.dirname(self._dsPaths['runtime_file']), exist_ok=True)
        iUmask = os.umask(0o077)
        oFile = None
        try:
            oFile = open(self._dsPaths['runtime_file'], 'w')
            oFile.write(self._oResource.toString(True))
        finally:
            if oFile: oFile.close()
            os.umask(iUmask)


    def loadRuntime(self):
        """
        Restore the resource runtime configuration and status from file

        @exception OSError       On runtime file I/O error
        @exception RuntimeError  On resource error
        """
        if self._iVerbose: self._DEBUG('Loading runtime')

        with open(self._dsPaths['runtime_file'], 'r') as oFile:
            oRuntimeConfig = RawConfigParser()
            oRuntimeConfig.optionxform = lambda sOption: sOption  # do not lowercase option (key) name
            oRuntimeConfig.read_file(oFile, self._dsPaths['runtime_file'])
        self._oResource = kiscResource(self._oResource.type(), self._oResource.id(), {tOption[0]: tOption[1] for tOption in oRuntimeConfig.items(self._oResource.id())})
        self._oResource.VERBOSE(self._iVerbose)


    def deleteRuntime(self):
        """
        Delete the resource runtime configuration and status file

        @exception OSError  Runtime file I/O error
        """
        if self._iVerbose: self._DEBUG('Deleting runtime')

        os.unlink(self._dsPaths['runtime_file'])


    #
    # Resource
    #

    def start(self, _bForce = False):
        """
        Start the resource

        @param bool _bForce  Forcefully start the resource (allow consumables oversubscription)

        @return list  Empty if resource is successfully started, (ordered) error messages otherwise
        """
        if self._iVerbose: self._INFO('Starting')
        lsErrors = list()

        # Start the resource
        bForceStopOnError = False
        try:

            # ... localhost ?
            if self._sHost_id != self._oClusterConfig.getHostByHostname().id():
                raise RuntimeError('Cannot start resource on remote host')

            # ... check host status
            from KiSC.Cluster.host import KiscCluster_host
            oClusterHost = KiscCluster_host(self._oClusterConfig, self._sHost_id)
            oClusterHost.VERBOSE(self._iVerbose)
            if not self._bBootstrap:
                if oClusterHost.status(True, KiscRuntime.STATUS_STARTED) != KiscRuntime.STATUS_STARTED:
                    raise RuntimeError('Host not started')

            # ... already started (potentially elsewhere) ?
            if not self._bBootstrap:
                iStatus = self.status(False, KiscRuntime.STATUS_STARTED)
                if iStatus == KiscRuntime.STATUS_STARTED:
                    if self._iVerbose: self._INFO('Resource already started')
                    return lsErrors
                if iStatus != KiscRuntime.STATUS_STOPPED:
                    raise RuntimeError('Resource not stopped')

            # ... host match ?
            if not self._oClusterConfig.isHostResource(self._sHost_id, self._sResource_id, self._bBootstrap):
                raise RuntimeError('Resource is not allowed to run on host')

            # ... registration delegation ?
            sHostRegistration_id = self._sHost_id
            if not self._bBootstrap:
                sHostRegistration_id = oClusterHost.host().registerTo()
                if sHostRegistration_id is not None:
                    if oClusterHost.host().isVirtual():
                        raise RuntimeError('Virtual host may not delegate registration to other host')
                    oClusterHost = KiscCluster_host(self._oClusterConfig, sHostRegistration_id)
                    oClusterHost.VERBOSE(self._iVerbose)
                    if not oClusterHost.host().isVirtual():
                        raise RuntimeError('Host may not delegate registration to non-virtual host')
                    if oClusterHost.status(True, KiscRuntime.STATUS_STARTED) != KiscRuntime.STATUS_STARTED:
                        raise RuntimeError('Registration host not started')

            # ... check the host's resources (consumables availability)
            if self._oResource.config().get('CONSUMES', None) is not None:
                lsErrors_sub = oClusterHost.registerResource(self._oResource, self._bBootstrap, _bCheck = True, _bOversubscribe = _bForce)
                if lsErrors_sub:
                    lsErrors.extend(lsErrors_sub)
                    raise RuntimeError('Host\'s resources registration check failed')

            # ... cache the resource internals
            (lsErrors_sub, ltCacheFiles) = self._oResource.cache(self._oClusterConfig.getDirectoryCache())
            if lsErrors_sub:
                lsErrors.extend(lsErrors_sub)
                raise RuntimeError('Failed to cache resource internals')
            for tCacheFile in ltCacheFiles:
                self._oClusterConfig.resolveFile(tCacheFile[0], tCacheFile[1], sHostRegistration_id, self._sResource_id, self._bBootstrap, tCacheFile[2])

            # ... on error, forcefully stop the resource from this point on
            bForceStopOnError = True

            # ... start the resource
            lsErrors_sub = self._oResource.start()
            if lsErrors_sub:
                lsErrors.extend(lsErrors_sub)
                raise RuntimeError('Failed to start resource')

            # ... register the host's resource
            lsErrors_sub = oClusterHost.registerResource(self._oResource, self._bBootstrap, _bOversubscribe = _bForce)
            if lsErrors_sub:
                lsErrors.extend(lsErrors_sub)
                raise RuntimeError('Failed to register to the host\'s resources')

            # ... register the resource's host
            lsErrors_sub = self._oResource.registerHost(oClusterHost.host())
            if lsErrors_sub:
                lsErrors.extend(lsErrors_sub)
                raise RuntimeError('Failed to register the resource\'s host')

            # ... save runtime configuration and status to file
            self.saveRuntime()

            # ... done
            if self._iVerbose: self._INFO('Started')
            
        except (OSError, RuntimeError) as e:
            if self._iVerbose: self._ERROR(str(e))
            lsErrors.append(str(e))
            if bForceStopOnError: self.stop(True)

        # Done
        return lsErrors


    def suspend(self):
        """
        Suspend the resource

        @return list  Empty if resource is successfully stopped, (ordered) error messages otherwise
        """
        if self._iVerbose: self._INFO('Suspending')
        lsErrors = list()

        # Suspend the resource
        try:

            # ... bootstrap ?
            if self._bBootstrap:
                raise RuntimeError('Bootstrap resource may not be suspended')

            # ... localhost ?
            if self._sHost_id != self._oClusterConfig.getHostByHostname().id():
                raise RuntimeError('Cannot suspend resource on remote host')

            # ... check host status
            from KiSC.Cluster.host import KiscCluster_host
            oClusterHost = KiscCluster_host(self._oClusterConfig, self._sHost_id)
            oClusterHost.VERBOSE(self._iVerbose)
            if oClusterHost.status(True, KiscRuntime.STATUS_STARTED) != KiscRuntime.STATUS_STARTED:
                raise RuntimeError('Host not started')

            # ... started / already suspended (locally) ?
            iStatus = self.status(True, KiscRuntime.STATUS_SUSPENDED)
            if iStatus == KiscRuntime.STATUS_SUSPENDED:
                if self._iVerbose: self._INFO('Resource already suspended')
                return lsErrors
            if iStatus != KiscRuntime.STATUS_STARTED:
                raise RuntimeError('Resource not started (locally)')

            # ... suspend the resource
            lsErrors_sub = self._oResource.suspend()
            if lsErrors_sub:
                lsErrors.extend(lsErrors_sub)
                raise RuntimeError('Failed to suspend resource')

            # ... save runtime configuration and status to file
            self.saveRuntime()

            # ... done
            if self._iVerbose: self._INFO('Suspended')

        except (OSError, RuntimeError) as e:
            if self._iVerbose: self._ERROR(str(e))
            lsErrors.append(str(e))

        # Done
        return lsErrors


    def resume(self):
        """
        Resume the resource

        @return list  Empty if resource is successfully resumed, (ordered) error messages otherwise
        """
        if self._iVerbose: self._INFO('Resuming')
        lsErrors = list()

        # Resume the resource
        try:

            # ... bootstrap ?
            if self._bBootstrap:
                raise RuntimeError('Bootstrap resource may not be resumed')

            # ... localhost ?
            if self._sHost_id != self._oClusterConfig.getHostByHostname().id():
                raise RuntimeError('Cannot resume resource on remote host')

            # ... check host status
            from KiSC.Cluster.host import KiscCluster_host
            oClusterHost = KiscCluster_host(self._oClusterConfig, self._sHost_id)
            oClusterHost.VERBOSE(self._iVerbose)
            if oClusterHost.status(True, KiscRuntime.STATUS_STARTED) != KiscRuntime.STATUS_STARTED:
                raise RuntimeError('Host not started')

            # ... suspended / already started (locally) ?
            iStatus = self.status(True, KiscRuntime.STATUS_STARTED)
            if iStatus == KiscRuntime.STATUS_STARTED:
                if self._iVerbose: self._INFO('Resource is started')
                return lsErrors
            if iStatus != KiscRuntime.STATUS_SUSPENDED:
                raise RuntimeError('Resource not suspended (locally)')

            # ... resume the resource
            lsErrors_sub = self._oResource.resume()
            if lsErrors_sub:
                lsErrors.extend(lsErrors_sub)
                raise RuntimeError('Failed to resume resource')

            # ... save runtime configuration and status to file
            self.saveRuntime()

            # ... done
            if self._iVerbose: self._INFO('Resumed')

        except (OSError, RuntimeError) as e:
            if self._iVerbose: self._ERROR(str(e))
            lsErrors.append(str(e))

        # Done
        return lsErrors


    def stop(self, _bForce = False):
        """
        Stop the resource

        @param bool _bForce  Forcefully stop the resource, ignoring non-critical errors

        @return list  Empty if resource is successfully stopped, (ordered) error messages otherwise
        """
        if self._iVerbose: self._INFO('Stopping')
        lsErrors = list()

        # Stop the resource
        bForceStopOnError = False
        try:

            # ... localhost ?
            if self._sHost_id != self._oClusterConfig.getHostByHostname().id():
                raise RuntimeError('Cannot stop resource on remote host')

            # ... check host status
            from KiSC.Cluster.host import KiscCluster_host
            oClusterHost = KiscCluster_host(self._oClusterConfig, self._sHost_id)
            oClusterHost.VERBOSE(self._iVerbose)
            if not self._bBootstrap:
                if oClusterHost.status(True, KiscRuntime.STATUS_STARTED) != KiscRuntime.STATUS_STARTED:
                    raise RuntimeError('Host not started')

            # ... already stopped (locally) ?
            iStatus = self.status(True, KiscRuntime.STATUS_STOPPED)
            if iStatus == KiscRuntime.STATUS_STOPPED:
                if not self._bBootstrap and not _bForce:
                    raise RuntimeError('Resource not started (locally)')
                elif self._iVerbose: self._WARNING('Resource not started')

            # ... registration delegation ?
            sHostRegistration_id = self._sHost_id
            if not self._bBootstrap:
                sHostRegistration_id = oClusterHost.host().registerTo()
                if sHostRegistration_id is not None:
                    oClusterHost = KiscCluster_host(self._oClusterConfig, sHostRegistration_id)
                    oClusterHost.VERBOSE(self._iVerbose)
                    if oClusterHost.status(True, KiscRuntime.STATUS_STARTED) != KiscRuntime.STATUS_STARTED:
                        raise RuntimeError('Registration host not started')

            # ... stop the resource
            lsErrors_sub = self._oResource.stop()
            if lsErrors_sub:
                if not _bForce:
                    lsErrors.extend(lsErrors_sub)
                    raise RuntimeError('Failed to stop resource')
                elif self._iVerbose: self._WARNING('Failed to stop resource')

            # ... on error, forcefully stop the resource from this point on
            bForceStopOnError = True

            # ... unregister the resource's host
            lsErrors_sub = self._oResource.unregisterHost(oClusterHost.host())
            if lsErrors_sub:
                if not _bForce:
                    lsErrors.extend(lsErrors_sub)
                    raise RuntimeError('Failed to unregister the resource\'s host')
                elif self._iVerbose: self._WARNING('Failed to unregister the resource\'s host')

            # ... unregister the host's resource
            lsErrors_sub = oClusterHost.unregisterResource(self._oResource, self._bBootstrap)
            if lsErrors_sub:
                if not _bForce:
                    lsErrors.extend(lsErrors_sub)
                    raise RuntimeError('Failed to unregister to the host\'s resources')
                elif self._iVerbose: self._WARNING('Failed to unregister from the host\'s resources')

            # ... delete runtime file
            if self.existsRuntime():
                self.deleteRuntime()

            # ... done
            if self._iVerbose: self._INFO('Stopped')

        except (OSError, RuntimeError) as e:
            if self._iVerbose: self._ERROR(str(e))
            lsErrors.append(str(e))
            if bForceStopOnError: self.stop(True)

        # Done
        return lsErrors


    def migrate(self, _sHost_id, _bForce = False):
        """
        Migrate the resource to the given host

        @param bool _bForce  Forcefully migrate the resource (allow consumables oversubscription)

        @return list  Empty if resource is successfully migrated, (ordered) error messages otherwise
        """
        if self._iVerbose: self._INFO('Migrating')
        lsErrors = list()

        # Migrate the resource
        bForceStopOnError = False
        try:

            # ... bootstrap ?
            if self._bBootstrap:
                raise RuntimeError('Bootstrap resource may not be migrated')

            # ... localhost ?
            if self._sHost_id != self._oClusterConfig.getHostByHostname().id():
                raise RuntimeError('Cannot migrate resource from remote host')

            # ... same host ?
            if self._sHost_id == _sHost_id:
                raise RuntimeError('Cannot migrate resource from/to same host')

            # ... check (local) host status
            from KiSC.Cluster.host import KiscCluster_host
            oClusterHost_local = KiscCluster_host(self._oClusterConfig, self._sHost_id)
            oClusterHost_local.VERBOSE(self._iVerbose)
            if oClusterHost_local.status(True, KiscRuntime.STATUS_STARTED) != KiscRuntime.STATUS_STARTED:
                raise RuntimeError('Local host not started')

            # ... started (locally) ?
            iStatus = self.status(True, KiscRuntime.STATUS_STARTED)
            if iStatus != KiscRuntime.STATUS_STARTED:
                raise RuntimeError('Resource not started (locally)')

            # ... (remote) host match ?
            if not self._oClusterConfig.isHostResource(_sHost_id, self._sResource_id):
                raise RuntimeError('Resource is not allowed to run on remote host')

            # ... check (remote) host status
            from KiSC.Cluster.host import KiscCluster_host
            oClusterHost_remote = KiscCluster_host(self._oClusterConfig, _sHost_id)
            oClusterHost_remote.VERBOSE(self._iVerbose)
            if oClusterHost_remote.status(False, KiscRuntime.STATUS_STARTED) != KiscRuntime.STATUS_STARTED:
                raise RuntimeError('Remote host not started')

            # ... (local) registration delegation ?
            sHostRegistration_id = oClusterHost_local.host().registerTo()
            if sHostRegistration_id is not None:
                oClusterHost_local = KiscCluster_host(self._oClusterConfig, sHostRegistration_id)
                oClusterHost_local.VERBOSE(self._iVerbose)
                if oClusterHost_local.status(True, KiscRuntime.STATUS_STARTED) != KiscRuntime.STATUS_STARTED:
                    raise RuntimeError('Local registration host not started')

            # ... (remote) registration delegation ?
            sHostRegistration_id = oClusterHost_remote.host().registerTo()
            if sHostRegistration_id is not None:
                if oClusterHost_remote.host().isVirtual():
                    raise RuntimeError('Virtual host may not delegate registration to other host')
                oClusterHost_remote = KiscCluster_host(self._oClusterConfig, sHostRegistration_id)
                oClusterHost_remote.VERBOSE(self._iVerbose)
                if not oClusterHost_remote.host().isVirtual():
                    raise RuntimeError('Remote host may not delegate registration to non-virtual host')
                if oClusterHost_remote.status(True, KiscRuntime.STATUS_STARTED) != KiscRuntime.STATUS_STARTED:
                    raise RuntimeError('Remote registration host not started')

            # ... switch registration ?
            if oClusterHost_remote.host().id() != oClusterHost_local.host().id():
                bHostRegistration_switch = True
            else:
                bHostRegistration_switch = False

            # ... check the (remote) host's resources (consumables availability)
            if bHostRegistration_switch and self._oResource.config().get('CONSUMES', None) is not None:
                lsErrors_sub = oClusterHost_remote.registerResource(self._oResource, self._bBootstrap, _bCheck = True, _bOversubscribe = _bForce)
                if lsErrors_sub:
                    lsErrors.extend(lsErrors_sub)
                    raise RuntimeError('Remote host\'s resources registration check failed')

            # ... migrate the resource
            lsErrors_sub = self._oResource.migrate(oClusterHost_remote.host())
            if lsErrors_sub:
                lsErrors.extend(lsErrors_sub)
                raise RuntimeError('Failed to migrate resource')

            # ... on error, forcefully stop the resource from this point on
            bForceStopOnError = True

            # ... switch registration ?
            if bHostRegistration_switch:
                # ... unregister the resource's (local) host
                lsErrors_sub = self._oResource.unregisterHost(oClusterHost_local.host())
                if lsErrors_sub:
                    lsErrors.extend(lsErrors_sub)
                    raise RuntimeError('Failed to unregister the resource\'s local host')

                # ... unregister the (local) host's resource
                lsErrors_sub = oClusterHost_local.unregisterResource(self._oResource, self._bBootstrap)
                if lsErrors_sub:
                    lsErrors.extend(lsErrors_sub)
                    raise RuntimeError('Failed to unregister from the local host\'s resources')

                # ... register the (remote) host's resource
                lsErrors_sub = oClusterHost_remote.registerResource(self._oResource, self._bBootstrap, _bOversubscribe = _bForce)
                if lsErrors_sub:
                    lsErrors.extend(lsErrors_sub)
                    raise RuntimeError('Failed to pre-register to the remote host\'s resources')

                # ... register the resource's (remote) host
                lsErrors_sub = self._oResource.registerHost(oClusterHost_remote.host())
                if lsErrors_sub:
                    lsErrors.extend(lsErrors_sub)
                    raise RuntimeError('Failed to register the resource\'s remote host')

            # ... save runtime configuration and status to file
            self.saveRuntime()

            # ... done
            if self._iVerbose: self._INFO('Started')
            
        except (OSError, RuntimeError) as e:
            if self._iVerbose: self._ERROR(str(e))
            lsErrors.append(str(e))
            if bForceStopOnError: self.stop(True)

        # Done
        return lsErrors


    def status(self, _bLocal = False, _iIntent = None):
        """
        Query the resource status
        
        @param bool _bLocal   Query the resource local status (in addition to its global status)
        @param int  _iIntent  Intent (status) of the status check

        @return int  Resource status (see KiscRuntime.STATUS_* constants)
        """
        if self._iVerbose: self._INFO('Querying status')

        # Status check
        iStatus = KiscRuntime.STATUS_STOPPED
        try:

            bResource_runtime_file = self.existsRuntime()
            if bResource_runtime_file:
                self.loadRuntime()
            if _bLocal:
                iResource_status = self._oResource.status(True, _iIntent)
                if iResource_status == KiscRuntime.STATUS_UNKNOWN or iResource_status == KiscRuntime.STATUS_ERROR:
                    raise RuntimeError('Failed to query local resource status')
                bResource_started = (iResource_status != KiscRuntime.STATUS_STOPPED)
                if bResource_started:
                    if bResource_runtime_file:
                        if _iIntent != KiscRuntime.STATUS_STOPPED:
                            self.saveRuntime()  # self._oResource may have been updated by its status() call
                        iStatus = iResource_status
                    else:
                        raise RuntimeError('Resource started locally but not globally')
            elif bResource_runtime_file:
                iStatus = self._oResource.status(False, _iIntent)

        except (OSError, RuntimeError) as e:
            if self._iVerbose: self._ERROR(str(e))
            iStatus = KiscRuntime.STATUS_ERROR

        # Done
        if self._iVerbose: self._INFO('Status is %s' % KiscRuntime.STATUS_MESSAGE[iStatus])
        return iStatus
