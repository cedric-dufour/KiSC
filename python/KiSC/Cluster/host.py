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

class KiscCluster_host:
    """
    Cluster-level host object
    """

    #--------------------------------------------------------------------------
    # CONSTRUCTORS
    #--------------------------------------------------------------------------

    def __init__(self, _oClusterConfig, _sHost_id):
        # Properties
        self._oClusterConfig = _oClusterConfig
        self._sHost_id = _sHost_id
        self._oHost = self._oClusterConfig.getHost(_sHost_id)
        
        # ... paths
        sHost_runtime_dir = self._oClusterConfig.getDirectoryRuntimeGlobal()
        sHost_host_prefix = self._oHost.type()+':'+self._oHost.id()
        sHost_runtime_file = sHost_runtime_dir+os.sep+sHost_host_prefix+'.run'
        self._dsPaths = {
            'runtime_dir': sHost_runtime_dir,
            'host_prefix': sHost_host_prefix,
            'runtime_file': sHost_runtime_file,
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
        self._oHost.VERBOSE(self._iVerbose)


    def _ERROR(self, _sMessage):
        """
        Print ERROR message to standard error

        @param str _sMessage  Message to print
        """

        if(self._iVerbose >= KiscRuntime.VERBOSE_ERROR):
            sys.stderr.write('ERROR[CH:%s] %s\n' % (self._sHost_id, _sMessage.replace('\n', '¬')))


    def _WARNING(self, _sMessage):
        """
        Print WARNING message to standard error

        @param str _sMessage  Message to print
        """

        if(self._iVerbose >= KiscRuntime.VERBOSE_WARNING):
            sys.stderr.write('WARNING[CH:%s] %s\n' % (self._sHost_id, _sMessage.replace('\n', '¬')))


    def _INFO(self, _sMessage):
        """
        Print INFO message to standard error

        @param str _sMessage  Message to print
        """

        if(self._iVerbose >= KiscRuntime.VERBOSE_INFO):
            sys.stderr.write('INFO[CH:%s] %s\n' % (self._sHost_id, _sMessage.replace('\n', '¬')))


    def _DEBUG(self, _sMessage):
        """
        Print DEBUG message to standard error

        @param str _sMessage  Message to print
        """

        if(self._iVerbose >= KiscRuntime.VERBOSE_DEBUG):
            sys.stderr.write('DEBUG[CH:%s] %s\n' % (self._sHost_id, _sMessage.replace('\n', '¬')))


    #
    # Helpers
    #

    def host(self):
        """
        Return the host resource (object)

        @return KiscResource_cluster_host  Host resource object
        """

        return self._oHost


    def existsRuntime(self):
        """
        Return whether the host runtime configuration and status file exists

        @return bool  True is file exists, False otherwis

        @exception OSError  Runtime file I/O error
        """

        return os.path.isfile(self._dsPaths['runtime_file'])


    def saveRuntime(self):
        """
        Save the host runtime configuration and status to file

        @exception OSError  Runtime file I/O error
        """
        if self._iVerbose: self._DEBUG('Saving runtime')

        os.makedirs(os.path.dirname(self._dsPaths['runtime_file']), exist_ok=True)
        iUmask = os.umask(0o077)
        oFile = None
        try:
            oFile = open(self._dsPaths['runtime_file'], 'w')
            oFile.write(self._oHost.toString(True))
        finally:
            if oFile: oFile.close()
            os.umask(iUmask)


    def loadRuntime(self):
        """
        Restore the host runtime configuration and status from file

        @exception OSError       On runtime file I/O error
        @exception RuntimeError  On host resource error
        """
        if self._iVerbose: self._DEBUG('Loading runtime')

        with open(self._dsPaths['runtime_file'], 'r') as oFile:
            oRuntimeConfig = RawConfigParser()
            oRuntimeConfig.optionxform = lambda sOption: sOption  # do not lowercase option (key) name
            oRuntimeConfig.read_file(oFile, self._dsPaths['runtime_file'])
        self._oHost = kiscResource(self._oHost.type(), self._oHost.id(), {tOption[0]: tOption[1] for tOption in oRuntimeConfig.items(self._oHost.id())})
        self._oHost.VERBOSE(self._iVerbose)


    def deleteRuntime(self):
        """
        Delete the host runtime configuration and status file

        @exception OSError  Runtime file I/O error
        """
        if self._iVerbose: self._DEBUG('Deleting runtime')

        os.unlink(self._dsPaths['runtime_file'])


    #
    # Host
    #

    def start(self):
        """
        Start the host

        @return list  Empty if host is successfully started, (ordered) error messages otherwise
        """
        if self._iVerbose: self._INFO('Starting')
        lsErrors = list()

        # Start the host
        try:

            # ... virtual ?
            bVirtual = self._oHost.isVirtual()
            
            # ... localhost ?
            sHost_id = self._oHost.id()
            sLocalhost_id = self._oClusterConfig.getHostByHostname().id()
            if not bVirtual:
                if sHost_id != sLocalhost_id:
                    raise RuntimeError('Cannot start remote host')
            else:
                dsConfig = self._oHost.config()
                if 'HOSTS' in dsConfig and not self._oClusterConfig.isHostAllowed(dsConfig['HOSTS'], sLocalhost_id):
                    raise RuntimeError('Local host (%s) not allowed to handle this (virtual) host' % sLocalhost_id)

            # ... initialize runtime configuration and status from/to file
            if self.existsRuntime():
                self.loadRuntime()
            else:
                self.saveRuntime()

            # ... start the host's bootstrap resources
            if not bVirtual:
                from KiSC.Cluster.resource import KiscCluster_resource
                for sResource_id in self._oClusterConfig.getResourcesIDs(True):
                    if not self._oClusterConfig.isHostResource(sHost_id, sResource_id, True):
                        continue
                    oClusterResource = KiscCluster_resource(self._oClusterConfig, sHost_id, sResource_id, True)
                    oClusterResource.VERBOSE(self._iVerbose)
                    lsErrors_sub = oClusterResource.start()
                    if lsErrors_sub:
                        lsErrors.extend(lsErrors_sub)
                        raise RuntimeError('Failed to start host\'s bootstrap resource (%s)' % sResource_id)

                # ... refresh runtime configuration and status to file
                self.loadRuntime()

            # ... start the host resource
            lsErrors_sub = self._oHost.start()
            if lsErrors_sub:
                lsErrors.extend(lsErrors_sub)
                raise RuntimeError('Failed to start host resource')

            # ... save runtime configuration and status to file
            self.saveRuntime()

            # ... done
            if self._iVerbose: self._INFO('Started')

        except (OSError, RuntimeError) as e:
            if self._iVerbose: self._ERROR(str(e))
            lsErrors.append(str(e))
            self.stop(True)

        # Done
        return lsErrors


    def stop(self, _bForce = False):
        """
        Stop the host

        @param bool _bForce  Forcefully stop the host, ignoring non-critical errors

        @return list  Empty if host is successfully stopped, (ordered) error messages otherwise
        """
        if self._iVerbose: self._INFO('Stopping')
        lsErrors = list()

        # Stop the host
        try:

            # ... virtual ?
            bVirtual = self._oHost.isVirtual()

            # ... localhost ?
            sHost_id = self._oHost.id()
            sLocalhost_id = self._oClusterConfig.getHostByHostname().id()
            if not bVirtual:
                if sHost_id != sLocalhost_id:
                    raise RuntimeError('Cannot stop remote host')
            else:
                dsConfig = self._oHost.config()
                if 'HOSTS' in dsConfig and not self._oClusterConfig.isHostAllowed(dsConfig['HOSTS'], sLocalhost_id):
                    raise RuntimeError('Local host (%s) not allowed to handle this (virtual) host' % sLocalhost_id)

            # ... runtime status check
            bHost_runtime_file = self.existsRuntime()
            if not bHost_runtime_file and not _bForce:
                raise RuntimeError('Host not started')

            # ... load runtime configuration and status from file
            if bHost_runtime_file:
                self.loadRuntime()

            # ... check/stop the host's (regular) resources
            if len(self._oHost.getResourcesIDs(_bBootstrap = False)):
                if not _bForce:
                    raise RuntimeError('Resources are running on host')
                from KiSC.Cluster.resource import KiscCluster_resource
                for sResource_id in reversed(self._oHost.getResourcesIDs(_bBootstrap = False)):
                    if not self._oClusterConfig.isHostResource(sHost_id, sResource_id, _bBootstrap = False):
                        continue
                    oClusterResource = KiscCluster_resource(self._oClusterConfig, sHost_id, sResource_id, _bBootstrap = False)
                    oClusterResource.VERBOSE(self._iVerbose)
                    lsErrors_sub = oClusterResource.stop(_bForce)
                    if lsErrors_sub:
                        lsErrors.extend(lsErrors_sub)
                        raise RuntimeError('Failed to stop host\'s resource (%s)' % sResource_id)

            # ... stop the host resource
            lsErrors_sub = self._oHost.stop()
            if lsErrors_sub and not _bForce:
                lsErrors.extend(lsErrors_sub)
                raise RuntimeError('Failed to stop host resource')

            # ... update runtime configuration and status from file
            if bHost_runtime_file:
                self.saveRuntime()

            # ... stop the host's bootstrap resources
            if not bVirtual:
                from KiSC.Cluster.resource import KiscCluster_resource
                for sResource_id in reversed(self._oHost.getResourcesIDs(_bBootstrap = True)):
                    if not self._oClusterConfig.isHostResource(sHost_id, sResource_id, _bBootstrap = True):
                        continue
                    oClusterResource = KiscCluster_resource(self._oClusterConfig, sHost_id, sResource_id, _bBootstrap = True)
                    oClusterResource.VERBOSE(self._iVerbose)
                    if not KiscRuntime.parseBool(oClusterResource.resource().config().get('PERSISTENT', False)):
                        lsErrors_sub = oClusterResource.stop(_bForce)
                        if lsErrors_sub:
                            lsErrors.extend(lsErrors_sub)
                            raise RuntimeError('Failed to stop host\'s bootstrap resource (%s)' % sResource_id)

            # ... delete runtime file
            if bHost_runtime_file:
                os.unlink(self._dsPaths['runtime_file'])

            # ... done
            if self._iVerbose: self._INFO('Stopped')

        except (OSError, RuntimeError) as e:
            if self._iVerbose: self._ERROR(str(e))
            lsErrors.append(str(e))

        # Done
        return lsErrors


    def status(self, _bLocal = False, _iIntent = None):
        """
        Query the host status
        
        @param bool _bLocal   Query the resource local status (in addition to its global status)
        @param int  _iIntent  Intent (status) of the status check

        @return int  Host status (see KiscRuntime.STATUS_* constants)
        """
        if self._iVerbose: self._INFO('Querying status')

        # Status check
        iStatus = KiscRuntime.STATUS_STOPPED
        try:

            bHost_runtime_file = self.existsRuntime()
            if bHost_runtime_file:
                self.loadRuntime()
            if _bLocal:
                iHost_status = self._oHost.status(True, _iIntent)
                if iHost_status == KiscRuntime.STATUS_UNKNOWN or iHost_status == KiscRuntime.STATUS_ERROR:
                    raise RuntimeError('Failed to query local host status')
                bHost_started = (iHost_status != KiscRuntime.STATUS_STOPPED)
                if bHost_started:
                    if bHost_runtime_file:
                        iStatus = iHost_status
                    else:
                        raise RuntimeError('Host started locally but not globally')
            elif bHost_runtime_file:
                iStatus = self._oHost.status(False, _iIntent)

        except (OSError, RuntimeError) as e:
            if self._iVerbose: self._ERROR(str(e))
            iStatus = KiscRuntime.STATUS_ERROR

        # Done
        if self._iVerbose: self._INFO('Status is %s' % KiscRuntime.STATUS_MESSAGE[iStatus])
        return iStatus


    #
    # Registration
    #

    def registerResource(self, _oResource, _bBootstrap = False, _bCheck = False, _bOversubscribe = False):
        """
        Register the given resource (as running on this host)

        @param KiscResource _oResource       Resource (object) to register
        @param bool         _bBootstrap      Register bootstrap (host startup) resource
        @param bool         _bCheck          Dry-run/check registration (consumables availability)
        @param bool         _bOversubscribe  Allow consumables oversubscription (DANGEROUS)

        @return list  Empty if resource is successfully registered, (ordered) error messages otherwise
        """
        if self._iVerbose: self._INFO('Registering resource (%s)%s' % (_oResource.id(), ' [CHECK]' if _bCheck else ''))
        lsErrors = list()

        # Register resource
        try:

            # ... virtual ?
            bVirtual = self._oHost.isVirtual()

            # ... registration delegation ?
            if not _bBootstrap and self._oHost.registerTo() is not None:
                raise SystemError('Resource registration delegated to other host')

            # ... runtime status check
            if not self.existsRuntime():
                raise RuntimeError('Host not started')

            # ... load runtime configuration and status from file
            self.loadRuntime()

            # ... register resource
            lsErrors_sub = self._oHost.registerResource(_oResource, _bBootstrap, _bCheck, _bOversubscribe)
            if lsErrors_sub:
                lsErrors.extend(lsErrors_sub)
                raise RuntimeError('Failed to register host\'s resource (%s)' % _oResource.id())

            # ... check ?
            if _bCheck:
                return lsErrors

            # ... save runtime configuration and status to file
            self.saveRuntime()

            # ... done
            if self._iVerbose: self._INFO('Resource registered (%s)' % _oResource.id())

        except RuntimeError as e:
            if self._iVerbose: self._ERROR(str(e))
            lsErrors.append(str(e))

        # Done
        return lsErrors


    def unregisterResource(self, _oResource, _bBootstrap = False):
        """
        Unregister the given resource (as running on this host)

        @param KiscResource _oResource   Resource (object) to unregister
        @param bool         _bBootstrap  Unregister bootstrap (host startup) resource

        @return list  Empty if resource is successfully unregistered, (ordered) error messages otherwise
        """
        if self._iVerbose: self._INFO('Unregistering resource (%s)' % _oResource.id())
        lsErrors = list()

        # Unregister resource
        try:

            # ... virtual ?
            bVirtual = self._oHost.isVirtual()

            # ... registration delegation ?
            if not _bBootstrap and self._oHost.registerTo() is not None:
                raise SystemError('Resource registration delegated to other host')

            # ... runtime status check
            if not self.existsRuntime():
                raise RuntimeError('Host not started')

            # ... load runtime configuration and status from file
            self.loadRuntime()

            # ... unregister resource
            lsErrors_sub = self._oHost.unregisterResource(_oResource, _bBootstrap)
            if lsErrors_sub:
                lsErrors.extend(lsErrors_sub)
                raise RuntimeError('Failed to unregister host\'s resource (%s)' % _oResource.id())

            # ... save runtime configuration and status to file
            self.saveRuntime()

            # ... done
            if self._iVerbose: self._INFO('Resource unregistered (%s)' % _oResource.id())

        except RuntimeError as e:
            if self._iVerbose: self._ERROR(str(e))
            lsErrors.append(str(e))

        # Done
        return lsErrors
