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
import socket


#------------------------------------------------------------------------------
# CLASSES
#------------------------------------------------------------------------------

class KiscResource_cluster_host(KiscResource):
    """
    Cluster host

    Configuration parameters are:
     - [REQUIRED] hostname (STRING):
       host name (preferrably fully-qualified hostname, FQDN)
     - [OPTIONAL] aliases (STRING; comma-separated):
       host aliases (e.g. short name, cluster node name, etc.)
     - [OPTIONAL] virtual (*no|yes):
       virtual host (to be used along 'register_to' hosts; see below)
     - [OPTIONAL] CONSUMABLES (STRING; comma-separated <consumable-id>:<quantity> pairs):
       list of provided consumables quantity
     - [OPTIONAL] register_to (STRING; host ID):
       delegate resources registration to the given (virtual) host
    """


    #--------------------------------------------------------------------------
    # CONSTRUCTORS
    #--------------------------------------------------------------------------

    def __init__(self, _sId, _dsConfig):
        KiscResource.__init__(self, _sId, _dsConfig)

        # Properties
        self._bInitialized = False
        self._sHostname = None  # lazily initialized
        self._lsAliases = None  # lazily initialized
        self._diConsumables = None  # lazily initialized
        self._diConsumables_used = None  # lazily initialized
        self._bVirtual = None  # lazily initialized
        self._sResisterAs_id = None  # lazily initialized


    def _initProperties(self):
        # Hostname
        self._sHostname = self._dsConfig['hostname']
        # ... aliases
        self._lsAliases = KiscRuntime.parseList(self._dsConfig.get('aliases', None))

        # Consumables
        # ... available
        self._diConsumables = KiscRuntime.parseDictionary(self._dsConfig.get('CONSUMABLES', None), -1, int)
        # ... consumed
        self._diConsumables_used = KiscRuntime.parseDictionary(self._dsConfig.get('$CONSUMABLES_USED', None), 1, int)

        # Virtual <-> Registration
        self._bVirtual = KiscRuntime.parseBool(self._dsConfig.get('virtual', False))
        self._sRegisterTo_id = self._dsConfig.get('register_to', None)

        # Done
        self._bInitialized = True


    #--------------------------------------------------------------------------
    # METHODS: KiscResource (implemented/overriden)
    #--------------------------------------------------------------------------

    def type(self):
        return 'cluster_host'


    def verify(self):
        lsErrors = list()
        if not len(self._dsConfig.get('hostname', str())):
            lsErrors.append('Invalid resource configuration; missing "hostname" setting')
        return lsErrors


    def start(self):
        if self._iVerbose: self._INFO('Starting')
        lsErrors = list()

        # Be idempotent
        if self.status(True, KiscRuntime.STATUS_STARTED) == KiscRuntime.STATUS_STARTED:
            if self._iVerbose: self._INFO('Already started')
            return lsErrors

        # Start the host
        try:

            # ... lazy initialization
            if not self._bInitialized:
                self._initProperties()

            # ... localhost ?
            sHostname_local = socket.getfqdn()
            if not self._bVirtual:
                if sHostname_local != self._sHostname and sHostname_local not in self._lsAliases:
                    raise RuntimeError('Cannot start remote host')

            # ... done
            self._iStatus = KiscRuntime.STATUS_STARTED
            if self._iVerbose: self._INFO('Started')

        except RuntimeError as e:
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

        # Stop the host
        try:

            # ... lazy initialization
            if not self._bInitialized:
                self._initProperties()

            # ... localhost ?
            sHostname_local = socket.getfqdn()
            if not self._bVirtual:
                if sHostname_local != self._sHostname and sHostname_local not in self._lsAliases:
                    raise RuntimeError('Cannot stop remote host')

            # ... check registration status
            if len(self._dsConfig.get('$RESOURCES', str())):
                raise RuntimeError('Resources are running')

            # ... done
            self._iStatus = KiscRuntime.STATUS_STOPPED
            if self._iVerbose: self._INFO('Stopped')

        except RuntimeError as e:
            if self._iVerbose: self._ERROR(str(e))
            self._iStatus = KiscRuntime.STATUS_ERROR
            lsErrors.append(str(e))

        # Done
        return lsErrors


    def status(self, _bStateful = True, _iIntent = None):
        if self._iVerbose: self._INFO('Querying status')
        iStatus = self._iStatus

        if _bStateful:

            # Query the host status
            try:

                # ... lazy initialization
                if not self._bInitialized:
                    self._initProperties()

                # ... localhost ?
                if not self._bVirtual:
                    sHostname_local = socket.getfqdn()
                    if sHostname_local == self._sHostname or sHostname_local in self._lsAliases:
                        if iStatus == KiscRuntime.STATUS_UNKNOWN:
                            iStatus = KiscRuntime.STATUS_STOPPED
                    else:
                        iStatus = KiscRuntime.STATUS_UNKNOWN
                else:
                    if iStatus == KiscRuntime.STATUS_UNKNOWN:
                        iStatus = KiscRuntime.STATUS_STOPPED

            except OSError as e:
                if self._iVerbose: self._ERROR(str(e))
                iStatus = KiscRuntime.STATUS_ERROR

        else:
            iStatus = self._iStatus 

        # Done
        self._iStatus = iStatus
        if self._iVerbose: self._INFO('Status is %s' % KiscRuntime.STATUS_MESSAGE[self._iStatus])
        return self._iStatus


    #--------------------------------------------------------------------------
    # METHODS: self
    #--------------------------------------------------------------------------

    #
    # Host
    #

    def getHostname(self):
        """
        Return the host name

        @return str  Host name
        """

        if not self._bInitialized:
            self._initProperties()
        return self._sHostname


    def getAliases(self):
        """
        Return the host aliases

        @return list  Host aliases (list)
        """

        if not self._bInitialized:
            self._initProperties()
        return self._lsAliases


    def isVirtual(self):
        """
        Return whether the host is virtual

        @return bool  True is host is virtual, False otherwise
        """

        if not self._bInitialized:
            self._initProperties()
        return self._bVirtual


    #
    # Registration
    #


    def registerTo(self):
        """
        Return the host (ID) where resources ought to be registered

        @return str  Host ID, None if registration is not delegated
        """

        if not self._bInitialized:
            self._initProperties()
        return self._sRegisterTo_id
        

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
            sResource_id = _oResource.id()

            # ... lazy initialization
            if not self._bInitialized:
                self._initProperties()

            # ... virtual ?
            if self._bVirtual and _bBootstrap:
                raise SystemError('Virtual host may not register bootstrap resource')

            # ... registered resources
            if _bBootstrap:
                lsResources = KiscRuntime.parseList(self._dsConfig.get('$BOOTSTRAP', None))
            else:
                lsResources = KiscRuntime.parseList(self._dsConfig.get('$RESOURCES', None))

            # ... check registration status
            if sResource_id in lsResources:
                if self._iVerbose and not _bCheck: self._INFO('Resource already registered (%s)' % _oResource.id())
                return lsErrors

            # ... check consumables
            diConsumables_used = dict()
            diConsumes = KiscRuntime.parseDictionary(_oResource._dsConfig.get('CONSUMES', None), 1, int)
            for sConsumable_id in diConsumes:
                iConsumable_wanted = diConsumes[sConsumable_id]
                if sConsumable_id in self._diConsumables:
                    iConsumable_available = self._diConsumables[sConsumable_id]
                else:
                    if self._iVerbose: self._WARNING('Consumable not available (%s)' % sConsumable_id)
                    continue
                if iConsumable_available >= 0:
                    if sConsumable_id in self._diConsumables_used:
                        iConsumable_used = self._diConsumables_used[sConsumable_id]
                    else:
                        iConsumable_used = 0
                    iConsumable_remaining = iConsumable_available-iConsumable_used
                    if iConsumable_wanted > iConsumable_remaining:
                        if _bOversubscribe:
                            if self._iVerbose and not _bCheck: self._WARNING('Consumable oversubscription (%s); %d > %d' % (sConsumable_id, iConsumable_used+iConsumable_wanted, iConsumable_available))
                        else:
                            raise RuntimeError('Consumable exhausted (%s)' % sConsumable_id)
                diConsumables_used[sConsumable_id] = iConsumable_wanted

            # ... check ?
            if _bCheck:
                return lsErrors

            # ... finalize
            for sConsumable_id in diConsumables_used:
                if self._iVerbose: self._DEBUG('Registering consumable (%s:%d)' % (sConsumable_id, diConsumables_used[sConsumable_id]))
                if sConsumable_id in self._diConsumables_used:
                    self._diConsumables_used[sConsumable_id] += diConsumables_used[sConsumable_id]
                else:
                    self._diConsumables_used[sConsumable_id] = diConsumables_used[sConsumable_id]
            lsResources.append(sResource_id)
            if _bBootstrap:
                self._dsConfig['$BOOTSTRAP'] = ','.join(lsResources)
            else:
                self._dsConfig['$RESOURCES'] = ','.join(lsResources)
            if len(self._diConsumables_used):
                self._dsConfig['$CONSUMABLES_USED'] = ','.join(['%s:%d' % (k, self._diConsumables_used[k]) for k in sorted(self._diConsumables_used.keys())])
            self._dsConfig['$CONSUMABLES_FREE'] = ','.join(['%s:%d' % (k, self._diConsumables[k] - self._diConsumables_used.get(k, 0)) for k in sorted(self._diConsumables.keys())])
            if self._iVerbose: self._INFO('Resource registered (%s)' % _oResource.id())

        except RuntimeError as e:
            if self._iVerbose: self._ERROR(str(e))
            lsErrors.append(str(e))

        # Done
        return lsErrors


    def unregisterResource(self, _oResource, _bBootstrap = False):
        """
        Unregister the given resource (as running on this host)

        @param KiscResource  _oResource   Resource (object) to unregister
        @param bool          _bBootstrap  Unregister bootstrap (host startup) resource

        @return list  Empty if resource is successfully unregistered, (ordered) error messages otherwise
        """
        if self._iVerbose: self._INFO('Unregistering resource (%s)' % _oResource.id())
        lsErrors = list()

        # Unregister resource
        try:
            sResource_id = _oResource.id()

            # ... lazy initialization
            if not self._bInitialized:
                self._initProperties()

            # ... virtual ?
            if self._bVirtual and _bBootstrap:
                raise SystemError('Virtual host may not unregister bootstrap resource')

            # ... registered resources
            if _bBootstrap:
                lsResources = KiscRuntime.parseList(self._dsConfig.get('$BOOTSTRAP', None))
            else:
                lsResources = KiscRuntime.parseList(self._dsConfig.get('$RESOURCES', None))

            # ... check registration status
            if sResource_id not in lsResources:
                if self._iVerbose: self._INFO('Resource not registered (%s)' % _oResource.id())
                return lsErrors

            # ... consumables
            diConsumables_used = dict()
            diConsumes = KiscRuntime.parseDictionary(_oResource._dsConfig.get('CONSUMES', None), 1, int)
            for sConsumable_id in diConsumes:
                if sConsumable_id not in self._diConsumables_used:
                    if self._iVerbose: self._WARNING('Consumable not registered (%s)' % sConsumable_id)
                    continue
                iConsumable_wanted = diConsumes[sConsumable_id]
                diConsumables_used[sConsumable_id] = iConsumable_wanted

            # ... finalize
            for sConsumable_id in diConsumables_used:
                if self._iVerbose: self._DEBUG('Unregistering consumable (%s:%d)' % (sConsumable_id, diConsumables_used[sConsumable_id]))
                self._diConsumables_used[sConsumable_id] -= diConsumables_used[sConsumable_id]
                if self._diConsumables_used[sConsumable_id] == 0:
                    del self._diConsumables_used[sConsumable_id]
            lsResources.remove(sResource_id)
            if _bBootstrap:
                self._dsConfig['$BOOTSTRAP'] = ','.join(lsResources)
                if not len(self._dsConfig['$BOOTSTRAP']):
                    del self._dsConfig['$BOOTSTRAP']
            else:
                self._dsConfig['$RESOURCES'] = ','.join(lsResources)
                if not len(self._dsConfig['$RESOURCES']):
                    del self._dsConfig['$RESOURCES']
            self._dsConfig['$CONSUMABLES_USED'] = ','.join(['%s:%d' % (k, self._diConsumables_used[k]) for k in sorted(self._diConsumables_used.keys())])
            if not len(self._dsConfig['$CONSUMABLES_USED']):
                del self._dsConfig['$CONSUMABLES_USED']
            self._dsConfig['$CONSUMABLES_FREE'] = ','.join(['%s:%d' % (k, self._diConsumables[k] - self._diConsumables_used.get(k, 0)) for k in sorted(self._diConsumables.keys())])
            if self._iVerbose: self._INFO('Resource unregistered (%s)' % _oResource.id())

        except RuntimeError as e:
            if self._iVerbose: self._ERROR(str(e))
            lsErrors.append(str(e))

        # Done
        return lsErrors


    def getResourcesIDs(self, _bBootstrap = False):
        """
        Return running resources (IDs)

        @param bool _bBootstrap  Return bootstrap (host startup) resource

        @return list  Running resources IDs
        """

        if _bBootstrap:
            return KiscRuntime.parseList(self._dsConfig.get('$BOOTSTRAP', None))
        else:
            return KiscRuntime.parseList(self._dsConfig.get('$RESOURCES', None))


    def getConsumables(self):
        """
        Return provided consumables quantity

        A negative consumable quantity means it is illimited.

        @return dict  Dictionary associating consumables ID and and their provided quantity
        """

        if not self._bInitialized:
            self._initProperties()
        return self._diConsumables


    def getConsumablesUsed(self):
        """
        Return used consumables quantity

        @return dict  Dictionary associating consumables ID and and their used quantity
        """

        if not self._bInitialized:
            self._initProperties()
        return self._diConsumables_used


    def getConsumablesFree(self):
        """
        Return free consumables quantity

        @return dict  Dictionary associating consumables ID and and their free quantity
        """

        if not self._bInitialized:
            self._initProperties()
        return {k: self._diConsumables[k] - self._diConsumables_used.get(k, 0) for k in sorted(self._diConsumables.keys())}
