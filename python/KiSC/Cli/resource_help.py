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
     KiscCluster_resource
from KiSC.Resource import \
     kiscResourceClass

# Standard
import pydoc
import textwrap
import sys


#------------------------------------------------------------------------------
# CLASSES
#------------------------------------------------------------------------------

class KiscCli_resource_help(KiscCli_kisc):
    """
    KiSC command-line utility - (Sub)command 'resource help'
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
                  display help on the given resource type
            ''')
        )

        # Arguments
        self._addOptionConfig(self._oArgumentParser)
        self._addOptionBootstrap(self._oArgumentParser)
        self._oArgumentParser.add_argument(
            '--type', action='store_true',
            help='consider specified resource as resource type rather than ID'
        )
        self._addArgumentResource(self._oArgumentParser)


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

        # Display resource help
        try:

            # Resource type
            if self._oArguments.type:
                sType = self._oArguments.resource
            else:
                # Load config
                oClusterConfig = KiscCluster_config(self._oArguments.config)
                lsErrors = oClusterConfig.load()
                if lsErrors:
                    sys.stderr.write('%s\n' % lsErrors[-1])
                    return 255

                # Retrieve host
                sHost_id = oClusterConfig.getHostByHostname().id()

                # Retrieve resource type
                sResource_id = self._oArguments.resource
                oClusterResource = KiscCluster_resource(oClusterConfig, sHost_id, sResource_id, self._oArguments.bootstrap)
                sType = oClusterResource.resource().type()

            # Show resource (type) help
            for sLine in pydoc.render_doc(kiscResourceClass(sType)).splitlines():
                if sLine.find('Method resolution order') >= 0:
                    break
                sys.stdout.write('%s\n' % sLine)
                
        except (OSError, RuntimeError) as e:
            sys.stderr.write('%s\n' % str(e))
            return 255

        # Done
        return 0
