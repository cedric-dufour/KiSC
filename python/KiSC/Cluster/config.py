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
from KiSC import \
     KISC_CONFIG_FILE, \
     KISC_CACHE_DIR, \
     KISC_LOCAL_RUNTIME_DIR, \
     KISC_GLOBAL_RUNTIME_DIR
from KiSC.Resource import \
     kiscResource
from KiSC.Runtime import \
     KiscRuntime

# Standard
import configparser
import os
import os.path
import sys


#------------------------------------------------------------------------------
# CLASSES
#------------------------------------------------------------------------------

class KiscCluster_config:
    """
    Cluster configuration object
    """

    #--------------------------------------------------------------------------
    # CONSTRUCTORS
    #--------------------------------------------------------------------------

    def __init__(self, _sConfigFile = None):

        # Properties
        self._sConfigFile = _sConfigFile
        if self._sConfigFile is None:
            self._sConfigFile = KISC_CONFIG_FILE
        self._dsConfig = dict()

        # ... hosts
        self._doHosts = dict()
        self._doHostgroups = dict()

        # ... resources
        #     NOTE: We MUST preserve resources order AND be able to quickly locate a resource ID.
        #           Thus the list() for the former and the dict() for the latter
        self._loResources_bootstrap = list()
        self._diResources_bootstrap = dict()
        self._loResources = list()
        self._diResources = dict()

        # ... debugging
        self._iVerbose = KiscRuntime.VERBOSE_NONE


    def __str__(self):
        return self.toString()


    #--------------------------------------------------------------------------
    # METHODS: self
    #--------------------------------------------------------------------------

    def toString(self, _bIncludeStatus = False, _bStateful = False):
        """
        Return the resource configuration (and status) in a human-friendly string

        @return str  Resource configuration (and status)
        """

        # Configuration (and status) string

        # ... local
        s  = '********************************************************************************\n'
        s += '* Local Configuration (%s)\n' % self._sConfigFile
        s += '********************************************************************************\n'
        s += '\n'
        s += '[KiSC]\n'
        for sKey in sorted(self._dsConfig):
            s += '%s=%s\n' % (sKey, self._dsConfig[sKey])

        # ... hosts
        s += '\n'
        s += '********************************************************************************\n'
        s += '* Hosts\n'
        s += '********************************************************************************\n'
        for sId in sorted(self._doHosts):
            s += '\n'
            s += self._doHosts[sId].toString(_bIncludeStatus, _bStateful)

        # ... hostgroups
        s += '\n'
        s += '********************************************************************************\n'
        s += '* Hostgroups\n'
        s += '********************************************************************************\n'
        for sId in sorted(self._doHostgroups):
            s += '\n'
            s += self._doHostgroups[sId].toString(_bIncludeStatus, _bStateful)

        # ... resources (bootstrap)
        s += '\n'
        s += '********************************************************************************\n'
        s += '* Resources (bootstrap)\n'
        s += '********************************************************************************\n'
        for i in range(0, len(self._loResources_bootstrap)):
            s += '\n'
            s += self._loResources_bootstrap[i].toString(_bIncludeStatus, _bStateful)

        # ... resources
        s += '\n'
        s += '********************************************************************************\n'
        s += '* Resources\n'
        s += '********************************************************************************\n'
        for i in range(0, len(self._loResources)):
            s += '\n'
            s += self._loResources[i].toString(_bIncludeStatus, _bStateful)

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
            sys.stderr.write('ERROR[C] %s\n' % _sMessage)


    def _WARNING(self, _sMessage):
        """
        Print WARNING message to standard error

        @param str _sMessage  Message to print
        """

        if(self._iVerbose >= KiscRuntime.VERBOSE_WARNING):
            sys.stderr.write('WARNING[C] %s\n' % _sMessage)


    def _INFO(self, _sMessage):
        """
        Print INFO message to standard error

        @param str _sMessage  Message to print
        """

        if(self._iVerbose >= KiscRuntime.VERBOSE_INFO):
            sys.stderr.write('INFO[C] %s\n' % _sMessage)


    def _DEBUG(self, _sMessage):
        """
        Print DEBUG message to standard error

        @param str _sMessage  Message to print
        """

        if(self._iVerbose >= KiscRuntime.VERBOSE_DEBUG):
            sys.stderr.write('DEBUG[C] %s\n' % _sMessage)


    #
    # Setters
    #

    def load(self):
        """
        Load the configuration from disk

        @return list  Empty if resource is successfully started, (ordered) error messages otherwise
        """
        if self._iVerbose: self._INFO('Loading configuration')
        lsErrors = list()

        # Load configuration from disc
        try:
            # Defaults
            sDirectoryCache = KISC_CACHE_DIR
            sDirectoryRuntimeLocal = KISC_LOCAL_RUNTIME_DIR
            sDirectoryRuntimeGlobal = KISC_GLOBAL_RUNTIME_DIR

            # Load base configuration from file
            with open(self._sConfigFile, 'r') as oFile:
                oConfig = configparser.RawConfigParser()
                oConfig.read_file(oFile, self._sConfigFile)

            # Parse base configuration section (KiSC)
            if oConfig.has_section('KiSC'):
                if oConfig.has_option('KiSC', 'cache_dir'):
                    sDirectoryCache = oConfig.get('KiSC', 'cache_dir')
                if oConfig.has_option('KiSC', 'local_runtime_dir'):
                    sDirectoryRuntimeLocal = oConfig.get('KiSC', 'local_runtime_dir')
                if oConfig.has_option('KiSC', 'global_runtime_dir'):
                    sDirectoryRuntimeGlobal = oConfig.get('KiSC', 'global_runtime_dir')

            # Store base configuration
            self._dsConfig['config_file'] = self._sConfigFile
            self._dsConfig['cache_dir'] = sDirectoryCache
            self._dsConfig['local_runtime_dir'] = sDirectoryRuntimeLocal
            self._dsConfig['global_runtime_dir'] = sDirectoryRuntimeGlobal

            # Make sure local cache/runtime directories exists
            # NOTE: ideally, those are located on a tmpfs partition
            os.makedirs(self._dsConfig['cache_dir'], exist_ok=True)
            os.makedirs(self._dsConfig['local_runtime_dir'], exist_ok=True)

            # Loop through other sections/resources (IDs)
            lsErrors_sub = self.__loadResources(self._sConfigFile, True, True)
            if lsErrors_sub:
                lsErrors.extend(lsErrors_sub)

            # Done
            if self._iVerbose: self._INFO('Configuration loaded')

        except (OSError, configparser.Error, RuntimeError) as e:
            if self._iVerbose: self._ERROR(str(e))
            lsErrors.append(str(e))

        # Done
        return lsErrors


    def __loadResources(self, _sConfigFile, _bBootstrap = False, _bAutostart = False):
        """
        Load resources configuration from file

        @param str  _sConfigFile  Configuration file (path)
        @param bool _bBootstrap   Bootstrap (host startup) configuration
        @param bool _bAutostart   Automatically start bootstrap resources

        @return list  Empty if resource is successfully started, (ordered) error messages otherwise
        """
        if self._iVerbose: self._DEBUG('Loading resources configuration from file (%s)' % _sConfigFile)
        lsErrors = list()

        try:

            # Load configuration from file
            with open(_sConfigFile, 'r') as oFile:
                oConfig = configparser.RawConfigParser()
                oConfig.optionxform = lambda sOption: sOption  # do not lowercase option (key) name
                oConfig.read_file(oFile, _sConfigFile)

            # Loop through sections/resources (IDs)
            for sId in oConfig.sections():
                if sId == 'KiSC': continue
                dsConfig = {tOption[0]: tOption[1] for tOption in oConfig.items(sId)}
                if 'TYPE' not in dsConfig:
                    lsErrors.append('<%s> [%s] Invalid configuration section; missing "TYPE" parameter' % (_sConfigFile, sId))
                    continue

                if dsConfig['TYPE'] == 'include':
                    # Include configuration file(s)
                    bBootstrap_sub = KiscRuntime.parseBool(dsConfig.get('BOOTSTRAP', False))
                    bAutostart_sub = KiscRuntime.parseBool(dsConfig.get('AUTOSTART', False))
                    if 'file' in dsConfig:
                        lsErrors_sub = self.__loadResources(dsConfig['file'], bBootstrap_sub, bAutostart_sub)
                        if lsErrors_sub:
                            lsErrors.extend(['<%s> %s' % (_sConfigFile, sError) for sError in lsErrors_sub])
                    if 'directory' in dsConfig:
                        import glob
                        for sFile in glob.glob('%s/%s' % (dsConfig['directory'], dsConfig.get('glob', '*.cfg'))):
                            lsErrors_sub = self.__loadResources(sFile, bBootstrap_sub, bAutostart_sub)
                            if lsErrors_sub:
                                lsErrors.extend(['<%s> %s' % (_sConfigFile, sError) for sError in lsErrors_sub])

                else:

                    if _bBootstrap:
                        lsErrors_sub = self.__createResource_bootstrap(dsConfig['TYPE'], sId, dsConfig, _bAutostart)
                    else:
                        lsErrors_sub = self.__createResource(dsConfig['TYPE'], sId, dsConfig)
                    if lsErrors_sub:
                        lsErrors.extend(['<%s> %s' % (_sConfigFile, sError) for sError in lsErrors_sub])

        except (OSError, configparser.Error, RuntimeError) as e:
            if self._iVerbose: self._ERROR(str(e))
            lsErrors.append('<%s> %s' % (_sConfigFile, str(e)))

        # Done
        return lsErrors


    def __createResource_bootstrap(self, _sType, _sId, _dsConfig, _bAutostart = False):
        """
        Create and add bootstrap (host startup) resource to cluster configuration

        @param str  _sType       Resource type (as '<category>:<sub-type>')
        @param str  _sId         Resource ID
        @param dict _dsConfig    Resource configuration (dictionary)
        @param bool _bAutostart  Automatically start the resource

        @return list  Empty if resource is successfully started, (ordered) error messages otherwise
        """
        if self._iVerbose: self._DEBUG('Creating bootstrap resource (%s:%s)' % (_sType, _sId))
        lsErrors = list()

        try:

            # Create resource
            oResource = kiscResource(_sType, _sId, _dsConfig)
            oResource.VERBOSE(self._iVerbose)

            # Verify resource configuration
            lsErrors_sub = oResource.verify()
            if lsErrors_sub:
                lsErrors.extend(lsErrors_sub)
                raise RuntimeError('Invalid resource configuration')

            # Add resource
            if _sType == 'cluster_host':
                # ... host definition
                if _sId in self._doHosts:
                    raise RuntimeError('Host with same ID already exist')
                self._doHosts[_sId] = oResource
                _bAutostart = False
            elif _sType == 'cluster_hostgroup':
                # ... hostgroup definition
                if _sId in self._doHostgroups:
                    raise RuntimeError('Hosts group with same ID already exist')
                self._doHostgroups[_sId] = oResource
                _bAutostart = False
            else:
                # ... other resource
                if _sId in self._diResources_bootstrap:
                    raise RuntimeError('Resource with same ID already exist')
                self._loResources_bootstrap.append(oResource)
                self._diResources_bootstrap[_sId] = len(self._loResources_bootstrap)-1

            # Start resource
            if _bAutostart:
                lsErrors_sub = oResource.start()
                if lsErrors_sub:
                    lsErrors.extend(lsErrors_sub)
                    raise RuntimeError('Failed to start resource')

        except RuntimeError as e:
            if self._iVerbose: self._ERROR(str(e))
            lsErrors.append('[%s] %s' % (_sId, str(e)))

        # Done
        return lsErrors


    def __createResource(self, _sType, _sId, _dsConfig):
        """
        Create and add resource to cluster configuration

        @param str  _sType       Resource type (as '<category>:<sub-type>')
        @param str  _sId         Resource ID
        @param dict _dsConfig    Resource configuration (dictionary)

        @return list  Empty if resource is successfully started, (ordered) error messages otherwise
        """
        if self._iVerbose: self._DEBUG('Creating resource (%s:%s)' % (_sType, _sId))
        lsErrors = list()

        try:

            # Check resource category
            if _sType[:8] == 'cluster_':
                raise RuntimeError('Invalid resource type (%s); "cluster" resources can only be defined in bootstrap configuration' % _sType)

            # Create resource
            oResource = kiscResource(_sType, _sId, _dsConfig)
            oResource.VERBOSE(self._iVerbose)

            # Verify resource configuration
            lsErrors_sub = oResource.verify()
            if lsErrors_sub:
                lsErrors.extend(lsErrors_sub)
                raise RuntimeError('Invalid resource configuration')

            # Add resource
            if _sId in self._diResources:
                raise RuntimeError('Resource with same ID already exist')
            self._loResources.append(oResource)
            self._diResources[_sId] = len(self._loResources)-1

        except RuntimeError as e:
            if self._iVerbose: self._ERROR(str(e))
            lsErrors.append('[%s] %s' % (_sId, str(e)))

        # Done
        return lsErrors


    #
    # Helpers
    #

    def isHostAllowed(self, _sConfigHosts, _sHost_id):
        """
        Return whether the given host ID is allowed by the given 'HOSTS'
        configuration string

        The 'HOSTS' configuration (string) must be comma-separated list of:
         - host IDs
         - '@'-prefixed hostgroup IDs
         - '@ALL' for all hosts (the default)

        An exclamation mark (!) can prefix the host(group) name to negate
        the condition.

        @param str _sConfigHosts  'HOSTS' configuration string
        @param str _sHost_id      Host ID to verify match for

        @return bool  True if host is allowed, False otherwise
        """
        if self._iVerbose: self._DEBUG('Allowing host (%s <-> %s)' % (_sHost_id, _sConfigHosts))

        bAllowed = _sConfigHosts[0] == '!'
        asConfigHosts = [s.strip() for s in _sConfigHosts.split(',')]
        for sHost_id in asConfigHosts:
            bIfMatch = True
            if sHost_id[0] == '!':
                bIfMatch = False
                sHost_id = sHost_id[1:]
            if sHost_id == '@ALL':
                bAllowed = bIfMatch
                if not bIfMatch: break
            elif sHost_id[0] == '@':
                try:
                    oHostgroup = self.getHostgroup(sHost_id[1:])
                    if _sHost_id in oHostgroup.getHostsIDs():
                        bAllowed = bIfMatch
                        if not bIfMatch: break
                except KeyError:
                    pass
            elif sHost_id == _sHost_id:
                bAllowed = bIfMatch
                if not bIfMatch: break
        if self._iVerbose: self._DEBUG('Host allowed: %s' % bAllowed)
        return bAllowed


    #
    # Getters
    #

    def getDirectoryCache(self):
        """
        Get the cache directory

        @return str  Cache directory path
        """

        return self._dsConfig['cache_dir']


    def getDirectoryRuntimeLocal(self):
        """
        Get the local runtime directory

        @return str  Local runtime directory path
        """

        return self._dsConfig['local_runtime_dir']


    def getDirectoryRuntimeGlobal(self):
        """
        Get the global runtime directory

        @return str  Global runtime directory path
        """

        return self._dsConfig['global_runtime_dir']


    def getHosts(self):
        """
        Get all host resources

        @return list  Hosts (resource) objects list
        """

        return self._doHosts.values()


    def getHostsIDs(self):
        """
        Get all host IDs

        @return list  Hosts IDs
        """

        return self._doHosts.keys()


    def getHost(self, _sHost_id):
        """
        Get host by given ID

        @param str _sHost_id  Host ID

        @return KiscResource_cluster_host  Host (resource) object

        @exception RuntimeError  If host cannot be found
        """

        if _sHost_id not in self._doHosts:
            raise RuntimeError('Host not found (%s)' % _sHost_id)
        return self._doHosts[_sHost_id]


    def getHostByHostname(self, _sHostname = None):
        """
        Get host by given name (hostname), the local hostname if omitted

        @param str _sHostname  Host name (e.g as returned by socket.getfqdn())

        @return KiscResource_cluster_host  Host (resource) object

        @exception RuntimeError  If host cannot be found
        """

        if _sHostname is None:
            import socket
            _sHostname = socket.getfqdn()
        for oHost in self._doHosts.values():
            if _sHostname == oHost.getHostname():
                return oHost
            elif _sHostname in oHost.getAliases():
                return oHost
            
        raise RuntimeError('Host (name) not found (%s)' % _sHostname)


    def getHostgroup(self, _sHostgroup_id):
        """
        Get hosts group by given ID

        @param str _sHostgroup_id  Hosts group ID

        @return KiscResource_cluster_hostgroup  Hosts group (resource) object

        @exception RuntimeError  If host group cannot be found
        """

        if _sHostgroup_id not in self._doHostgroups:
            raise RuntimeError('Host group not found (%s)' % _sHostgroup_id)
        return self._doHostgroups[_sHostgroup_id]


    def getResources(self, _bBootstrap = False):
        """
        Get all resources, ordered as per configuration file(s)

        WARNING: Resource IDs may not be unique (e.g. given resource scoped to different hosts)

        @param bool _bBootstrap  Whether to consider bootstrap (host startup) resources

        @return list  Resource objects list
        """

        if _bBootstrap:
            return self._loResources_bootstrap
        else:
            return self._loResources


    def getResourcesIDs(self, _bBootstrap = False):
        """
        Get all resources IDs, ordered as per configuration file(s)

        WARNING: Resource IDs may not be unique (e.g. given resource scoped to different hosts)

        @param bool _bBootstrap  Whether to consider bootstrap (host startup) resources

        @return list  Resource IDs
        """

        if _bBootstrap:
            return [oResource.id() for oResource in self._loResources_bootstrap]
        else:
            return [oResource.id() for oResource in self._loResources]


    def getResource(self, _sResource_id, _bBootstrap = False):
        """
        Get resource by given ID

        @param str  _sResource_id  Resource ID
        @param bool _bBootstrap    Whether to consider bootstrap (host startup) resources

        @return KiscResource  Resource object

        @exception RuntimeError  If resource cannot be found
        """

        if _bBootstrap:
            if _sResource_id not in self._diResources_bootstrap:
                raise RuntimeError('Resource (bootstrap) not found (%s)' % _sResource_id)
            return self._loResources_bootstrap[self._diResources_bootstrap[_sResource_id]]
        else:
            if _sResource_id not in self._diResources:
                raise RuntimeError('Resource not found (%s)' % _sResource_id)
            return self._loResources[self._diResources[_sResource_id]]


    def isHostResource(self, _sHost_id, _sResource_id, _bBootstrap = False):
        """
        Return whether the given resource is scoped to the given host

        @param str  _sHost_id      Host ID
        @param str  _sResource_id  Resource ID
        @param bool _bBootstrap    Whether to consider bootstrap (host startup) resources

        @return bool  True is resource is scoped for host, False otherwise

        @exception RuntimeError  If resource cannot be found
        """

        if _bBootstrap:
            if _sResource_id not in self._diResources_bootstrap:
                raise RuntimeError('Resource (bootstrap) not found (%s)' % _sResource_id)
            oResource = self._loResources_bootstrap[self._diResources_bootstrap[_sResource_id]]
            dsConfig = oResource.config()
            if 'HOSTS' in dsConfig:
                if self.isHostAllowed(dsConfig['HOSTS'], _sHost_id):
                    return True
            else:
                return True
        else:
            if _sResource_id not in self._diResources:
                raise RuntimeError('Resource not found (%s)' % _sResource_id)
            oResource = self._loResources[self._diResources[_sResource_id]]
            dsConfig = oResource.config()
            if 'HOSTS' in dsConfig:
                if self.isHostAllowed(dsConfig['HOSTS'], _sHost_id):
                    return True
            else:
                return True
        return False


    #
    # Variables resolution
    #

    def resolveString(self, _sString, _mHost = None, _mResource = None, _bBootstrap = False):
        """
        Resolve the cluster variables in the given string

        This method will resolve cluster variables defined as '%{<ID>[.<setting>][|<filter>][|...]}'.
        The following filter can be applied:
         - int, float, strip, lower, upper, dirname, basename
         - add(<int|float>), sub(<int|float>), mul(<int|float>), div(<int|float>)
         - remove(<str>), replace(<str>,<str>)

        @param  str  _sString     Input string
        @param  str  _mHost       Target host object or ID (substition for '$HOST' magic ID)
        @param  str  _mResource   Target resource object or ID (substition for '$SELF' magic ID)
        @param  bool _bBootstrap  Whether to consider bootstrap (host startup) resources

        @return str  String with cluster variables resolved

        @exception RuntimeError  On cluster variables subsitution error
        """
        if self._iVerbose: self._DEBUG('Resolving cluster variables string (%s)' % _sString)

        # 'HOST' host
        if _mHost is not None and type(_mHost) is str:
            _mHost = self.getHost(_mHost)

        # 'SELF' resource
        if _mResource is not None and type(_mResource) is str:
            _mResource = self.getResource(_mResource, _bBootstrap)

        # Prepare filter regexp
        import re
        lsRegexpFilters = [
            re.compile('(int|float|strip|lower|upper|dirname|basename)'),
            re.compile('(add|sub|mul|div)\( *([.0-9]+) *\)'),
            re.compile('(remove)\( *\'([^\']+)\' *\)'),
            re.compile('(replace)\( *\'([^\']+)\' *, *\'([^\']+)\' *\)'),
        ]

        # Look for cluster variables
        for sVariable in set(re.findall('%\{[^\{]*\}', _sString)):
            if self._iVerbose: self._DEBUG('Substituting variable (%s)' % sVariable)

            # ... split <resource-id>.<setting>
            try:
                (sResource_id, sSetting) = sVariable[2:-1].split('.')
            except ValueError as e:
                sResource_id = sVariable[2:-1]
                sSetting = 'ID'

            # ... apply filters
            lsSettingFilters = sSetting.split('|')
            if len(lsSettingFilters) > 1:
                sSetting = lsSettingFilters[0]

            # ... retrieve value
            try:

                # ... retrieve configuration
                if sResource_id == 'KiSC':
                    dsConfig = self._dsConfig
                elif sResource_id == '$HOST':
                    if _mHost is None:
                        raise RuntimeError('Target host not specified')
                    dsConfig = _mHost.config()
                elif sResource_id == '$SELF':
                    if _mResource is None:
                        raise RuntimeError('Target resource not specified')
                    dsConfig = _mResource.config()
                else:
                    try:
                        oResource_sub = self.getResource(sResource_id, False)
                    except RuntimeError as e:
                        oResource_sub = self.getResource(sResource_id, True)
                    dsConfig = oResource_sub.config()

                # ... retrieve configuration setting
                if sSetting[:8] == 'CONSUMES':
                    sConsumable_id = sSetting[9:-1]
                    diConsumables = KiscRuntime.parseDictionary(dsConfig['CONSUMES'], 1, int)
                    sValue = str(diConsumables[sConsumable_id])
                elif sSetting[:11] == 'CONSUMABLES':
                    sConsumable_id = sSetting[12:-1]
                    diConsumables = KiscRuntime.parseDictionary(dsConfig['CONSUMABLES'], 1, int)
                    sValue = str(diConsumables[sConsumable_id])
                else:
                    sValue = dsConfig[sSetting]

            except (RuntimeError, KeyError) as e:
                raise RuntimeError('Invalid cluster variable; %s (%s)' % (sVariable, str(e)))
            if self._iVerbose: self._DEBUG('Variable value is: %s' % sValue)

            # ... apply filters
            if len(lsSettingFilters) > 1:
                mValue = sValue
                try:
                    for sFilter in lsSettingFilters[1:]:
                        bMatched = False
                        for sRegexpFilter in lsRegexpFilters:
                            oMatch = sRegexpFilter.match(sFilter)
                            if oMatch is None:
                                continue
                            if self._iVerbose: self._DEBUG('Applying filter: %s' % sFilter)
                            bMatched = True
                            sOperator = oMatch.group(1)
                            tValue = type(mValue)
                            if sOperator == 'int':
                                mValue = int(mValue)
                            elif sOperator == 'float':
                                mValue = float(mValue)
                            elif sOperator == 'strip':
                                mValue = mValue.strip()
                            elif sOperator == 'lower':
                                mValue = mValue.lower()
                            elif sOperator == 'upper':
                                mValue = mValue.upper()
                            elif sOperator == 'dirname':
                                mValue = os.path.dirname(mValue)
                            elif sOperator == 'basename':
                                mValue = os.path.basename(mValue)
                            elif sOperator == 'add':
                                if tValue is float:
                                    mValue += float(oMatch.group(2))
                                else:
                                    mValue += int(oMatch.group(2))
                            elif sOperator == 'sub':
                                if tValue is float:
                                    mValue -= float(oMatch.group(2))
                                else:
                                    mValue -= int(oMatch.group(2))
                            elif sOperator == 'mul':
                                if tValue is float:
                                    mValue *= float(oMatch.group(2))
                                else:
                                    mValue *= int(oMatch.group(2))
                            elif sOperator == 'div':
                                if tValue is float:
                                    mValue /= float(oMatch.group(2))
                                else:
                                    mValue /= int(oMatch.group(2))
                            elif sOperator == 'remove':
                                mValue = mValue.replace(oMatch.group(2), '')
                            elif sOperator == 'replace':
                                mValue = mValue.replace(oMatch.group(2), oMatch.group(3))
                            break
                        if not bMatched:
                            raise RuntimeError(sFilter)
                    sValue = str(mValue)
                    if self._iVerbose: self._DEBUG('Final variable value is: %s' % sValue)
                except Exception as e:
                    raise RuntimeError('Invalid variable filter; %s' % str(e))

            # ... substitute value
            _sString = _sString.replace(sVariable, sValue)

        # Done
        if self._iVerbose: self._DEBUG('Resolved cluster variables string (%s)' % _sString)
        return _sString


    def resolveFile(self, _sFile_from, _sFile_to, _mHost = None, _mResource = None, _bBootstrap = False, _tPermissions = None):
        """
        Copy the given source file to the given destination, resolving cluster variables in their content

        This method will substitute cluster variables found in the file; see self.resolveString().

        @param  str  _sFile_from    Source file (standard input if None)
        @param  str  _sFile_to      Destination file (standard output if None)
        @param  str  _sHost_id      Target host ID (substition for '$HOST' magic ID)
        @param  str  _sResource_id  Target resource ID (substition for '$SELF' magic ID)
        @param  bool _bBootstrap    Whether to consider bootstrap (host startup) resources
        @param  tup  _tPermissions  Permissions tuple (<user>, <group>, <mode>)

        @exception OSError       On file I/O error
        @exception RuntimeError  On cluster variables subsitution errors
        """
        if self._iVerbose: self._INFO('Caching file: %s > %s' % (_sFile_from, _sFile_to))

        # Load source file
        if self._iVerbose: self._DEBUG('Reading file (%s)' % _sFile_from)
        if _sFile_from is None:
            sFile = sys.stdin.read()
        else:
            with open(_sFile_from, 'r') as oFile:
                sFile = oFile.read()

        # Resolve variables
        sFile = self.resolveString(sFile, _mHost, _mResource, _bBootstrap)

        # Save destination file
        if self._iVerbose: self._DEBUG('Writing file (%s)' % _sFile_to)
        if _sFile_to is None:
            sys.stdout.write(sFile)
        else:
            os.makedirs(os.path.dirname(_sFile_to), exist_ok=True)
            iUmask = os.umask(0o077)
            oFile = None
            try:
                oFile = open(_sFile_to, 'w')
                oFile.write(sFile)
                if _tPermissions is not None:
                    (mUser, mGroup, mMode) = _tPermissions
                    KiscRuntime.perms(oFile.fileno(), mUser, mGroup, mMode, _bTrace = self._iVerbose >= KiscRuntime.VERBOSE_TRACE)
            finally:
                if oFile: oFile.close()
                os.umask(iUmask)
