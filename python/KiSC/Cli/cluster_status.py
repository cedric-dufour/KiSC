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
     KiscCluster_config, \
     KiscCluster_host, \
     KiscCluster_resource
from KiSC.Runtime import \
     KiscRuntime

# Standard
import textwrap
import sys


#------------------------------------------------------------------------------
# CLASSES
#------------------------------------------------------------------------------

class KiscCli_cluster_status(KiscCli_kisc):
    """
    KiSC command-line utility - (Sub)command 'cluster status'
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
                  show hosts or resources status
            ''')
        )

        # Arguments
        self._addOptionConfig(self._oArgumentParser)
        self._addOptionVerbose(self._oArgumentParser)
        self._addOptionHost(self._oArgumentParser)
        self._addOptionResource(self._oArgumentParser)
        self._oArgumentParser.add_argument(
            'what', type=str, choices=['hosts', 'resources'], metavar='{hosts|resources}',
        )


    #
    # Execution
    #

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

        # Show cluster configuration
        try:

            # Load config
            oClusterConfig = KiscCluster_config(self._oArguments.config)
            lsErrors = oClusterConfig.load()
            if lsErrors:
                if self._oArguments.verbose >= KiscRuntime.VERBOSE_DEBUG:
                    for sError in lsErrors:
                        sys.stderr.write('%s\n' % sError)
                else:
                    sys.stderr.write('%s\n' % lsErrors[-1])
                return 255
            oClusterConfig.VERBOSE(self._oArguments.verbose)

            # Loop through hosts/resources
            if self._oArguments.what == 'hosts':
                if self._oArguments.host:
                    lsHosts_ids = [self._oArguments.host]
                else:
                    lsHosts_ids = sorted(oClusterConfig.getHostsIDs())
                for sHost_id in lsHosts_ids:
                    oClusterHost = KiscCluster_host(oClusterConfig, sHost_id)
                    oClusterHost.VERBOSE(self._oArguments.verbose)
                    iStatus = oClusterHost.status(False)
                    asResources_ids = oClusterHost.host().getResourcesIDs()
                    if self._oArguments.resource is None or self._oArguments.resource in asResources_ids:
                        sResources_ids = ','.join(asResources_ids)
                        sHostRegistration_id = oClusterHost.host().registerTo()
                        if sHostRegistration_id is not None:
                            sResources_ids = '> %s' % sHostRegistration_id
                        elif not len(sResources_ids):
                            sResources_ids = '-'
                        sys.stdout.write('%s %s %s\n' % (sHost_id, KiscRuntime.STATUS_MESSAGE[iStatus], sResources_ids))
            elif self._oArguments.what == 'resources':
                if self._oArguments.resource:
                    lsResources_ids = [self._oArguments.resource]
                else:
                    lsResources_ids = sorted(oClusterConfig.getResourcesIDs())
                for sResource_id in lsResources_ids:
                    oClusterResource = KiscCluster_resource(oClusterConfig, None, sResource_id, False)
                    oClusterResource.VERBOSE(self._oArguments.verbose)
                    iStatus = oClusterResource.status(False)
                    asHosts_ids = oClusterResource.resource().getHostsIDs()
                    if self._oArguments.host is None or self._oArguments.host in asHosts_ids:
                        sHosts_ids = ','.join(asHosts_ids)
                        if not len(sHosts_ids): sHosts_ids = '-'
                        sys.stdout.write('%s %s %s\n' % (sResource_id, KiscRuntime.STATUS_MESSAGE[iStatus], sHosts_ids))

        except (OSError, RuntimeError) as e:
            sys.stderr.write('%s\n' % str(e))
            return 255

        # Done
        return 0
