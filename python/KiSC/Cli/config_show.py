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
import textwrap
import sys


#------------------------------------------------------------------------------
# CLASSES
#------------------------------------------------------------------------------

class KiscCli_config_show(KiscCli_kisc):
    """
    KiSC command-line utility - (Sub)command 'config show'
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
                  show the cluster configuration
            ''')
        )

        # Arguments
        self._addOptionConfig(self._oArgumentParser)
        self._addOptionVerbose(self._oArgumentParser)
        self._addOptionHost(self._oArgumentParser)
        self._addOptionResource(self._oArgumentParser)
        self._addOptionBootstrap(self._oArgumentParser)


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
            oClusterConfig.VERBOSE(self._oArguments.verbose)
            lsErrors = oClusterConfig.load()
            if lsErrors:
                if self._oArguments.verbose >= KiscRuntime.VERBOSE_DEBUG:
                    for sError in lsErrors:
                        sys.stderr.write('%s\n' % sError)
                else:
                    sys.stderr.write('%s\n' % lsErrors[-1])
                return 255

            # Show config
            if self._oArguments.host:
                oHost = oClusterConfig.getHost(self._oArguments.host)
                sys.stdout.write(oHost.toString())
            elif self._oArguments.resource:
                oResource = oClusterConfig.getResource(self._oArguments.resource, self._oArguments.bootstrap)
                sys.stdout.write(oResource.toString())
            else:
                sys.stdout.write(oClusterConfig.toString())

        except (OSError, RuntimeError) as e:
            sys.stderr.write('%s\n' % str(e))
            return 255

        # Done
        return 0
