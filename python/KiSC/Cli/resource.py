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
from KiSC.Cli import \
     KiscCli_kisc

# Standard
import textwrap


#------------------------------------------------------------------------------
# CLASSES
#------------------------------------------------------------------------------

class KiscCli_resource(KiscCli_kisc):
    """
    KiSC command-line utility - Command 'resource'
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
                  resource management

                sub-commands:
                  start
                    start the resource
                  suspend
                    suspend the (started) resource
                  resume
                    resume the (suspended) resource
                  stop
                    stop the resource
                  status
                    query the resource status
                  runtime
                    show the resource configuration and runtime status
                  list
                    list resources (IDs) running on (local) host
                  help
                    display help on the given resource type
            ''')
        )

        # Additional arguments
        self._oArgumentParser.add_argument(
            'subcommand', type=str, metavar='<sub-command>'
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

        # Handle command
        self._oArgumentParser.print_help()
        return 0
