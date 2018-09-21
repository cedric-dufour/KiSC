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

# Standard
import sys


#------------------------------------------------------------------------------
# CLASSES
#------------------------------------------------------------------------------

class KiscResource:
    """
    Generic (virtual) resource class, mother of all actual resources classes
    (cluster, storage, network, services, etc.).
    """

    #--------------------------------------------------------------------------
    # CONSTRUCTORS
    #--------------------------------------------------------------------------

    def __init__(self, _sId, _dsConfig):
        """
        Instantiate a new resource

        @param str  _sId       Resource ID
        @param dict _dsConfig  Resource configuration (dictionary)
        """

        # Properties
        self._sId = _sId
        self._dsConfig = _dsConfig
        self._iStatus = KiscRuntime.STATUS_UNKNOWN

        # ... fill mandatory self.dump() fields
        self._dsConfig['TYPE'] = self.type()
        self._dsConfig['ID'] = self._sId

        # ... runtime
        if '$STATUS' not in self._dsConfig:
            self._dsConfig['$STATUS'] = KiscRuntime.STATUS_MESSAGE[self._iStatus]
        else:
            for iStatus in range(KiscRuntime.STATUS_UNKNOWN, KiscRuntime.STATUS_ERROR+1):
                if self._dsConfig['$STATUS'] == KiscRuntime.STATUS_MESSAGE[iStatus]:
                    self._iStatus = iStatus
                    break

        # ... debugging
        self._iVerbose = KiscRuntime.VERBOSE_NONE


    def __str__(self):
        return self.toString()


    #--------------------------------------------------------------------------
    # METHODS: self (implemented)
    #--------------------------------------------------------------------------

    def id(self):
        """
        Return the resource ID

        @return str  Resource ID
        """

        return self._sId


    def config(self, _bStateful = False):
        """
        Return the resource configuration and status

        This method returns a dictionary associating configuration setting
        names and their corresponding value.

        The following predefined keys are reserved and MUST be returned:
          'TYPE': the resource type
          'ID': the resource ID

        Keys starting with the dollar ($) signs are also reserved for runtime
        status and MAY NOT be used for configuration purposes.

        @param bool _bStateful  Return stateful (refreshed status) data

        @return dict  Configuration settings dictionary
        """


        if(_bStateful):
            self._iStatus = self.status(True)
        self._dsConfig['$STATUS'] = KiscRuntime.STATUS_MESSAGE[self._iStatus]
        return self._dsConfig


    def toString(self, _bIncludeStatus = False, _bStateful = False):
        """
        Return the resource configuration (and status) in a human-friendly string

        @param bool _bIncludeStatus  Include status data
        @param bool _bStateful       Return stateful (refreshed status) data

        @return str  Resource configuration (and status)
        """

        # Configuration (and status) string
        s = '[%s]\n' % self._sId
        s += 'TYPE=%s\n' % self.type()
        # ... configuration
        for sKey in sorted(self._dsConfig):
            if sKey[0] == '$' or sKey in ['ID', 'TYPE', 'STATUS']:
                continue
            s += '%s=%s\n' % (sKey, self._dsConfig[sKey])
        # ... runtime
        if _bIncludeStatus:
            if(_bStateful):
                self._iStatus = self.status(True)
            self._dsConfig['$STATUS'] = KiscRuntime.STATUS_MESSAGE[self._iStatus]
            for sKey in sorted(self._dsConfig):
                if sKey[0] != '$':
                    continue
                s += '%s=%s\n' % (sKey, self._dsConfig[sKey])

        # Done
        return s


    #
    # Debugging
    #

    def VERBOSE(self, _iVerbose):
        """
        Set verbosity level

        @param int _iVerbose  Verbosity level (self KiscRuntime.VERBOSE_* constants)
        """

        self._iVerbose = _iVerbose


    def _ERROR(self, _sMessage):
        """
        Print ERROR message to standard error

        @param str _sMessage  Message to print
        """

        if(self._iVerbose >= KiscRuntime.VERBOSE_ERROR):
            sys.stderr.write('ERROR[LR:%s:%s] %s\n' % (self.type(), self.id(), _sMessage.replace('\n', '¬')))


    def _WARNING(self, _sMessage):
        """
        Print WARNING message to standard error

        @param str _sMessage  Message to print
        """

        if(self._iVerbose >= KiscRuntime.VERBOSE_WARNING):
            sys.stderr.write('WARNING[LR:%s:%s] %s\n' % (self.type(), self.id(), _sMessage.replace('\n', '¬')))


    def _INFO(self, _sMessage):
        """
        Print INFO message to standard error

        @param str _sMessage  Message to print
        """

        if(self._iVerbose >= KiscRuntime.VERBOSE_INFO):
            sys.stderr.write('INFO[LR:%s:%s] %s\n' % (self.type(), self.id(), _sMessage.replace('\n', '¬')))


    def _DEBUG(self, _sMessage):
        """
        Print DEBUG message to standard error

        @param str _sMessage  Message to print
        """

        if(self._iVerbose >= KiscRuntime.VERBOSE_DEBUG):
            sys.stderr.write('DEBUG[LR:%s:%s] %s\n' % (self.type(), self.id(), _sMessage.replace('\n', '¬')))


    #--------------------------------------------------------------------------
    # METHODS: self (to be implemented)
    #--------------------------------------------------------------------------

    #
    # Resource
    #

    def type(self):
        """
        Return the resource type

        @return str  Resource type (category:sub-type)
        """

        raise SystemError('KiscResource.type() not implemented')


    def verify(self):
        """
        Verify the resource configuration (semantic)

        @return list  Empty if configuration passes verification,
                      (ordered) error messages otherwise
        """

        raise SystemError('KiscResource.verify() not implemented')


    def cache(self, _sDirectoryCache):
        """
        Cache the resource configuration files

        @param str _sDirectoryCache  Cache directory (path)

        @return (list, list)  1st tuple: Empty if caching is sucessfull, (ordered) error messages otherwise
                              2nd tuple: list of (sFrom, sTo, tPermissions) files to be cached by the cluster (see KiscCluster_config.resolveFile())
        """

        return (list(), list())


    def start(self):
        """
        Start the resource (idempotently)

        @return list  Empty if resource is successfully started, (ordered) error messages otherwise
        """

        raise SystemError('KiscResource.start() not implemented')


    def suspend(self):
        """
        Suspend the resource (idempotently)

        @return list  Empty if resource is successfully suspended, (ordered) error messages otherwise
        """

        raise SystemError('KiscResource.suspend() not implemented')


    def resume(self):
        """
        Resume the resource (idempotently)

        @return list  Empty if resource is successfully resumed, (ordered) error messages otherwise
        """

        raise SystemError('KiscResource.resume() not implemented')


    def stop(self):
        """
        Stop the resource (idempotently)

        @return list  Empty if resource is successfully stopped, (ordered) error messages otherwise
        """

        raise SystemError('KiscResource.stop() not implemented')


    def migrate(self, _oHost):
        """
        Migrate the resource to the given host (idempotently)

        @return list  Empty if resource is successfully migrated, (ordered) error messages otherwise
        """

        raise SystemError('KiscResource.migrate() not implemented')


    def status(self, _bStateful = True, _iIntent = None):
        """
        Query the resource status

        The implementation of this method MUST cache the queried status in the self._iStatus properties.
        The purpose status MAY be used to adapt the status check for a specific prupose; e.g. when stopping
        a resource, it may be desirable to perform only a "shallow" status check.

        @param bood _bStateful  Query the resource status (rather than just returning its cached value)
        @param int  _iIntent    Intent (status) of the status check

        @return int  Resource status (see KiscRuntime.STATUS_* constants)
        """

        raise SystemError('KiscResource.status() not implemented')


    #
    # Registration
    #

    def registerHost(self, _oHost):
        """
        Register the given host resource (as running this resource)

        @param KiscResource_cluster_host _oHost  Host resource (object) to register

        @return list  Empty if resource is successfully registered, (ordered) error messages otherwise
        """
        if self._iVerbose: self._INFO('Registering host (%s)' % _oHost.id())
        lsErrors = list()

        # Register host
        try:
            sHost_id = _oHost.id()

            # ... registered hosts
            lsHosts = KiscRuntime.parseList(self._dsConfig.get('$HOSTS', None))

            # ... check registration status
            if sHost_id in lsHosts:
                raise RuntimeError('Host already registered (%s)' % sHost_id)

            # ... finalize
            lsHosts.append(sHost_id)
            self._dsConfig['$HOSTS'] = ','.join(lsHosts)
            if self._iVerbose: self._INFO('Host registered  (%s)' % _oHost.id())

        except RuntimeError as e:
            if self._iVerbose: self._ERROR(str(e))
            lsErrors.append(str(e))

        # Done
        return lsErrors


    def unregisterHost(self, _oHost):
        """
        Unregister the given host resource (as running this resource)

        @param KiscResource_cluster_host _oHost  Host resource (object) to unregister

        @return list  Empty if resource is successfully unregistered, (ordered) error messages otherwise
        """
        if self._iVerbose: self._INFO('Unregistering host (%s)' % _oHost.id())
        lsErrors = list()

        # Unregister host
        try:
            sHost_id = _oHost.id()

            # ... registered hosts
            lsHosts = KiscRuntime.parseList(self._dsConfig.get('$HOSTS', None))

            # ... check registration status
            if sHost_id not in lsHosts:
                return lsErrors

            # ... finalize
            lsHosts.remove(sHost_id)
            self._dsConfig['$HOSTS'] = ','.join(lsHosts)
            if not len(self._dsConfig['$HOSTS']):
                del self._dsConfig['$HOSTS']
            if self._iVerbose: self._INFO('Host unregistered  (%s)' % _oHost.id())

        except RuntimeError as e:
            if self._iVerbose: self._ERROR(str(e))
            lsErrors.append(str(e))

        # Done
        return lsErrors


    def getHostsIDs(self):
        """
        Return hosts (IDs) running the resource

        @return list  Resource running hosts IDs
        """

        return KiscRuntime.parseList(self._dsConfig.get('$HOSTS', None))


#------------------------------------------------------------------------------
# FACTORY
#------------------------------------------------------------------------------

def kiscResourceClass(_sType):
    """
    Return the class matching the given resource type

    @param str _sType  Resource type (e.g. 'storage_mount')

    @return KiscResource  Resource class

    @exception RuntimeError  On type error
    """

    try:

        # Sanitize input
        import re
        if re.search('[^_a-z0-9]', _sType):
            raise RuntimeError('Invalid resource type (%s)' % _sType)

        # Import resource
        classResource = getattr(
            __import__(
                name='KiSC.Resource.%s' % _sType,
                fromlist=['KiSC'],
                level=0
            ),
            'KiscResource_%s' % _sType
        )
        return classResource

    except ImportError as e:
        raise RuntimeError('Invalid resource type (%s)' % _sType)


def kiscResource(_sType, _sId, _dsConfig):
    """
    Create a new resource

    @param str  _sType      Resource type (e.g. 'storage_mount')
    @param str  _sId        Resource ID
    @param dict _dsConfig   Resource configuration (dictionary)

    @return KiscResource  Resource object

    @exception RuntimeError  On type error
    """

    # Instantiate resource
    classResource = kiscResourceClass(_sType)
    oResource = classResource(_sId, _dsConfig)
    if oResource.type() != _sType:
        raise SystemError('Resource type mismatch (%s)' % _sType)
    return oResource
