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
     KiscCluster_host
from KiSC.Runtime import \
     KiscRuntime

# Standard
import textwrap
import sys


#------------------------------------------------------------------------------
# CLASSES
#------------------------------------------------------------------------------

class KiscCli_host_status(KiscCli_kisc):
    """
    KiSC command-line utility - (Sub)command 'host status'
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
                  query the host status; exit codes are:
                    0: started
                    1: stopped
                    2: error
            ''')
        )

        # Arguments
        self._addOptionConfig(self._oArgumentParser)
        self._addOptionSilent(self._oArgumentParser)
        self._addOptionVerbose(self._oArgumentParser)
        self._oArgumentParser.add_argument(
            '--local', action='store_true',
            help='query the host local status (in addition to its global status)'
        )
        self._addArgumentHost(self._oArgumentParser)


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

        # Query host status
        iStatus = KiscRuntime.STATUS_UNKNOWN
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

            # Retrieve host
            if self._oArguments.host:
                sHost_id = self._oArguments.host
            else:
                sHost_id = oClusterConfig.getHostByHostname().id()
            oClusterHost = KiscCluster_host(oClusterConfig, sHost_id)
            oClusterHost.VERBOSE(self._oArguments.verbose)

            # Query host status
            iStatus = oClusterHost.status(self._oArguments.local)
            if not self._oArguments.silent:
                sResources_ids = ','.join(oClusterHost.host().getResourcesIDs())
                sHostRegistration_id = oClusterHost.host().registerTo()
                if sHostRegistration_id is not None:
                    sResources_ids = '> %s' % sHostRegistration_id
                elif not len(sResources_ids):
                    sResources_ids = '-'
                sys.stdout.write('%s %s %s\n' % (sHost_id, KiscRuntime.STATUS_MESSAGE[iStatus], sResources_ids))

        except (OSError, RuntimeError) as e:
            sys.stderr.write('%s\n' % str(e))
            return 255

        # Done
        return iStatus
