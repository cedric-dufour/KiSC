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
     KISC_VERSION, \
     KISC_CONFIG_FILE
from KiSC.Runtime import \
     KiscRuntime

# Standard
import argparse
import errno
import os
import sys
import textwrap


#------------------------------------------------------------------------------
# CLASSES
#------------------------------------------------------------------------------

class KiscCli_kisc:
    """
    KiSC command-line utility (main entry point)
    """

    #--------------------------------------------------------------------------
    # METHODS
    #--------------------------------------------------------------------------

    #
    # Arguments (to be used by actual commands)
    #

    def _initArgumentParser(self, _sCommand=None, _sSynopsis=None):
        """
        Create the arguments parser (and help generator)

        @param str _sCommand   Command name
        @param str _sSynopsis  Additional help (synopsis)
        """

        # Command
        if _sCommand is None:
            _sCommand = sys.argv[0].split(os.sep)[-1]

        # Create argument parser
        if _sSynopsis is None:
            self._oArgumentParser = argparse.ArgumentParser(
                prog=_sCommand
            )
        else:
            self._oArgumentParser = argparse.ArgumentParser(
                prog=_sCommand,
                formatter_class=argparse.RawDescriptionHelpFormatter,
                epilog=_sSynopsis
            )

        # Standard arguments
        self._addOptionVersion(self._oArgumentParser)


    def _initArguments(self, _lArguments=None, _bAllowUnknownArguments=False):
        """
        Parse the command-line arguments

        @param list _lArguments              Command arguments
        @param bool _bAllowUnknownArguments  Allow unknown arguments

        @return list  List of unknown arguments (if allowed)
        """

        # Parse arguments
        lUnknownArguments = list()
        if _bAllowUnknownArguments:
            (self._oArguments, lUnknownArguments) = self._oArgumentParser.parse_known_args(_lArguments)
        else:
            self._oArguments = self._oArgumentParser.parse_args(_lArguments)
        return lUnknownArguments


    def _addOptionVersion(self, _oArgumentParser):
        """
        Adds the '--version' option to the given argument parser
        """

        # Add argument
        _oArgumentParser.add_argument(
            '-v', '--version', action='version',
            version=('KiSC - %s - (C) Idiap Research Institute <http://www.idiap.ch>\n' % KISC_VERSION)
        )


    def _addOptionConfig(self, _oArgumentParser):
        """
        Adds the '--config' option to the given argument parser
        """

        self._oArgumentParser.add_argument(
            '-C', '--config', type=str, metavar='<config-file>',
            default=KISC_CONFIG_FILE,
            help='cluster configuration file (default: %s)' % KISC_CONFIG_FILE
        )


    def _addOptionSilent(self, _oArgumentParser):
        """
        Adds the '--silent' option to the given argument parser
        """

        # Add argument
        _oArgumentParser.add_argument(
            '-S', '--silent', action='store_true',
            help='mute all standard output messages'
        )


    def _addOptionVerbose(self, _oArgumentParser):
        """
        Adds the '--verbose' option to the given argument parser
        """

        # Add argument
        _oArgumentParser.add_argument(
            '-V', '--verbose', type=int, metavar='<verbose-level>', default=0,
            help='set standard error verbosity level; 0=NONE ... %d=TRACE (default: 0)' % KiscRuntime.VERBOSE_TRACE
        )


    def _addArgumentHost(self, _oArgumentParser):
        """
        Adds the 'host' argument to the given argument parser
        """

        self._oArgumentParser.add_argument(
            'host', type=str, metavar='<host-id>', nargs='?',
            help='host identifier (ID; default: local host ID)'
        )


    def _addOptionHost(self, _oArgumentParser):
        """
        Adds the '--host' option to the given argument parser
        """

        self._oArgumentParser.add_argument(
            '-H', '--host', type=str, metavar='<host-id>',
            help='host identifier (ID)'
        )


    def _addArgumentResource(self, _oArgumentParser):
        """
        Adds the 'resource' argument to the given argument parser
        """

        self._oArgumentParser.add_argument(
            'resource', type=str, metavar='<resource-id>',
            help='resource identifier (ID)'
        )


    def _addOptionResource(self, _oArgumentParser):
        """
        Adds the '--resource' option to the given argument parser
        """

        self._oArgumentParser.add_argument(
            '-R', '--resource', type=str, metavar='<resource-id>',
            help='resource identifier'
        )


    def _addOptionBootstrap(self, _oArgumentParser):
        """
        Adds the '--bootstrap' option to the given argument parser
        """

        self._oArgumentParser.add_argument(
            '--bootstrap', action='store_true',
            help='bootstrap (host startup) resource(s)'
        )


    def _addOptionForce(self, _oArgumentParser):
        """
        Adds the '--force' option to the given argument parser
        """

        # Add argument
        _oArgumentParser.add_argument(
            '--force', action='store_true',
            help='force action (DANGEROUS!)'
        )


    #
    # Execution
    #

    def _help(self):
        """
        Show help (on stdout)
        """

        sys.stdout.write('usage: kisc <command> [<sub-command>]\n')
        sys.stdout.write(
            textwrap.dedent('''
                commands:
                  config
                    configuration management
                  cluster
                    cluster management
                  host
                    host management
                  resource
                    resource management

                help:
                  kisc <command> [<sub-command>] --help
            ''')
        )


    def execute(self):
        """
        Execute the command

        @return int  0 on success, non-zero in case of failure
        """

        try:

            # Check arguments
            if len(sys.argv)<=1:
                sys.stderr.write('ERROR: Too few arguments\n')
                return errno.EINVAL
            elif sys.argv[1] in ['help', '--help', '-h']:
                self._help()
                return 0

            # Parse command line
            sCommand_main = None
            sCommand_sub = None
            lArguments = list()
            for i in range(1, len(sys.argv)):
                s = sys.argv[i]
                if s[0]!='-':
                    if sCommand_main is None:
                        sCommand_main = s
                        continue
                    elif sCommand_sub is None:
                        sCommand_sub = s
                        continue
                lArguments += [s]

            # Sanitize input
            import re
            if re.search('[^a-z]', sCommand_main):
                raise RuntimeError('Invalid command')
            if sCommand_sub is not None and re.search('[^a-z]', sCommand_sub):
                raise RuntimeError('Invalid sub-command')

            # Instantiate command
            if sCommand_sub is None:
                sCommand = sCommand_main
                oCommand = getattr(
                    __import__(
                        'KiSC.Cli.%s' % sCommand_main,
                        fromlist=['KiSC'],
                        level=0
                    ),
                    'KiscCli_%s' % sCommand_main
                )
            else:
                sCommand = '%s %s' % (sCommand_main, sCommand_sub)
                oCommand = getattr(
                    __import__(
                        'KiSC.Cli.%s_%s' % (sCommand_main, sCommand_sub),
                        fromlist=['KiSC'],
                        level=0
                    ),
                    'KiscCli_%s_%s' % (sCommand_main, sCommand_sub)
                )

        except ImportError as e:
            sys.stderr.write('ERROR: Invalid (sub-)command\n')
            return errno.EINVAL
        except RuntimeError as e:
            sys.stderr.write('ERROR: %s\n' % str(e))
            raise e

        # Execute command
        try:
            return oCommand().execute('kisc %s' % sCommand, lArguments)
        except (OSError, RuntimeError) as e:
            sys.stderr.write('%s\n' % str(e))
            raise e


#------------------------------------------------------------------------------
# MAIN
#------------------------------------------------------------------------------

if __name__ == "__main__":
    try:
        sys.exit(KiscCli_kisc().execute())
    except OSError as e:
        sys.exit(e.errno)
    except RuntimeError as e:
        sys.exit(errno.EINVAL)
    except KeyboardInterrupt as e:
        sys.exit(-2)
