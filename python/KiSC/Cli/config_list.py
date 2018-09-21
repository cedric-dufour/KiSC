#!/usr/bin/env python3
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
     KISC_CONFIG_FILE
from KiSC.Cli import \
     KiscCli_kisc
from KiSC.Cluster import \
     KiscCluster_config
from KiSC.Runtime import \
     KiscRuntime

# Standard
import re
import textwrap
import sys


#------------------------------------------------------------------------------
# CLASSES
#------------------------------------------------------------------------------

class KiscCli_config_list(KiscCli_kisc):
    """
    KiSC command-line utility - (Sub)command 'config list'
    """

    #--------------------------------------------------------------------------
    # METHODS
    #--------------------------------------------------------------------------

    #
    # Arguments
    #

    def _initArgumentParser(self, _sCommand=None):
        """
        Create the arguments parser (and help generator)

        @param str _sCommand  Command name
        """

        # Parent
        KiscCli_kisc._initArgumentParser(
            self,
            _sCommand,
            textwrap.dedent('''
                synopsis:
                  list configured hosts or resources
            ''')
        )

        # Arguments
        self._addOptionConfig(self._oArgumentParser)
        self._addOptionBootstrap(self._oArgumentParser)
        self._oArgumentParser.add_argument(
            '-X', '--exclude', type=str, nargs='*', metavar='key{=value|~=regexp}',
            default=list(),
            help='exclude hosts/resources with matching setting(s) key/value'
        )
        self._oArgumentParser.add_argument(
            '-I', '--include', type=str, nargs='*', metavar='key{=value|~=regexp}',
            default=list(),
            help='include (only) hosts/resources with matching setting(s) key/value'
        )
        self._oArgumentParser.add_argument(
            'what', type=str, choices=['hosts', 'resources'], metavar='{hosts|resources}',
        )


    #
    # Execution
    #

    def _match(self, _dsConfig):
        """
        Return the given config is matched by user-specified filters
        """

        # Exclude
        for (sKey, mValue_filter) in self._ltFilters_exclude:
            if sKey in _dsConfig:
                if mValue_filter is None:
                    return False
                sValue = _dsConfig[sKey]
                if type(mValue_filter) is str:
                    if mValue_filter == sValue:
                        return False
                elif mValue_filter.search(sValue) is not None:
                    return False

        # Include
        if not len(self._ltFilters_include):
            return True
        for (sKey, mValue_filter) in self._ltFilters_include:
            if sKey not in _dsConfig:
                continue
            if mValue_filter is None:
                return True
            sValue = _dsConfig[sKey]
            if type(mValue_filter) is str:
                if mValue_filter == sValue:
                    return True
            elif mValue_filter.search(sValue) is not None:
                return True
        return False


    def execute(self, _sCommand=None, _lArguments=None):
        """
        Execute the command

        @param str  _sCommand    Command name
        @param list _lArguments  Command arguments

        @return int  0 on success, non-zero in case of failure
        """

        # Arguments
        self._initArgumentParser(_sCommand)
        self._initArguments(_lArguments)

        # List cluster hosts/resources
        try:

            # Filter
            # ... exclude
            self._ltFilters_exclude = list()
            for sFilter in self._oArguments.exclude:
                try:
                    (sKey, sValue) = sFilter.split('=', 1)
                    if sKey[-1] == '~':
                        sKey = sKey[:-1]
                        sValue = re.compile(sValue)
                except ValueError:
                    sKey = sFilter
                    sValue = None
                self._ltFilters_exclude.append((sKey, sValue))
            # ... include
            self._ltFilters_include = list()
            for sFilter in self._oArguments.include:
                try:
                    (sKey, sValue) = sFilter.split('=', 1)
                    if sKey[-1] == '~':
                        sKey = sKey[:-1]
                        sValue = re.compile(sValue)
                except ValueError:
                    sKey = sFilter
                    sValue = None
                self._ltFilters_include.append((sKey, sValue))

            # Load config
            oClusterConfig = KiscCluster_config(self._oArguments.config)
            lsErrors = oClusterConfig.load()
            if lsErrors:
                sys.stderr.write('%s\n' % lsErrors[-1])
                return 255

            # List IDs
            if self._oArguments.what == 'hosts':
                if not len(self._ltFilters_include) and not len(self._ltFilters_exclude):
                    sys.stdout.write('\n'.join(sorted(oClusterConfig.getHostsIDs()))+'\n')
                else:
                    for sHost_id in sorted(oClusterConfig.getHostsIDs()):
                        if self._match(oClusterConfig.getHost(sHost_id).config()):
                            sys.stdout.write('%s\n' % sHost_id)
            elif self._oArguments.what == 'resources':
                if not len(self._ltFilters_include) and not len(self._ltFilters_exclude):
                    sys.stdout.write('\n'.join(sorted(oClusterConfig.getResourcesIDs(self._oArguments.bootstrap)))+'\n')
                else:
                    for sResource_id in sorted(oClusterConfig.getResourcesIDs(self._oArguments.bootstrap)):
                        if self._match(oClusterConfig.getResource(sResource_id).config()):
                            sys.stdout.write('%s\n' % sResource_id)

        except (OSError, RuntimeError) as e:
            sys.stderr.write('%s\n' % str(e))
            return 255

        # Done
        return 0
