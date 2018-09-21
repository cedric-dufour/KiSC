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

# Standard
import errno
import os
import subprocess
import sys


#------------------------------------------------------------------------------
# CLASSES
#------------------------------------------------------------------------------

class KiscRuntime:
    """
    Global runtime environment and resources
    """

    #--------------------------------------------------------------------------
    # CONSTANTS
    #--------------------------------------------------------------------------

    # Verbosity
    VERBOSE_NONE = 0
    VERBOSE_ERROR = 1
    VERBOSE_WARNING = 2
    VERBOSE_INFO = 3
    VERBOSE_DEBUG = 4
    VERBOSE_TRACE = 5

    # Status
    STATUS_UNKNOWN = -1
    STATUS_STARTED = 0
    STATUS_SUSPENDED = 1
    STATUS_STOPPED = 2
    STATUS_ERROR = 3
    STATUS_MESSAGE = {
        STATUS_UNKNOWN: "Unknown",
        STATUS_STARTED: "Started",
        STATUS_SUSPENDED: "Suspended",
        STATUS_STOPPED: "Stopped",
        STATUS_ERROR: "Error",
        }


    #--------------------------------------------------------------------------
    # HELPERS
    #--------------------------------------------------------------------------

    def echo(_sString, _sFilename, _sMode = 'w', _bTrace = False):
        """
        Echo the given string into the given file

        @param str _sString    String to echo
        @param str _sFilename  File to echo into
        @param str _sMode      File opening mode
        @param bool _bTrace    Print TRACE message to standard error

        @exception OSError  On file I/O error
        """
        if _bTrace: sys.stderr.write('TRACE[echo] %s > %s (%s)\n' % (_sString, _sFilename, _sMode))

        # Open file
        oFile = open(_sFilename, _sMode)
        oFile.write(_sString)
        oFile.close()


    def shell(_llsCommands, _sWorkingDirectory = None, _bRedirectStdOut = True, _bIgnoreReturnCode = False, _bTrace = False):
        """
        Execute the given shell (piped) command(s) within the given working
        directory and returns the resulting standard output

        @param list _llsCommands        Command(s) path and arguments (as passed to Popen)
        @param str  _sWorkingDirectory  Directory to switch to before executing the command
        @param bool _bRedirectStdOut    Redirect standard output
        @param bool _bIgnoreReturnCode  Do not raise error in case of non-zero return code
        @param bool _bTrace             Print TRACE message to standard error

        @exception RuntimeError  On arguments error
        @exception OSError       In case a command returns a non-zero exit code, with the
                                 filename property set to the index of the erroneous command,
                                 starting from zero at the last command and increasing for
                                 previous (piped) commands

        @return str  Resulting standard output (if redirected), None otherwise
        """

        # Check
        if not _llsCommands:
            raise RuntimeError('Missing/empty command argument')

        # Handle single command
        if not type(_llsCommands[0]) is list:
            _llsCommands = [_llsCommands]
        if _bTrace: sys.stderr.write('TRACE[shell] %s\n' % ' | '.join([' '.join(lsCommand) for lsCommand in _llsCommands]))

        # Execute (piped) command(s)
        byStdOut = None
        iIndex_last = len(_llsCommands)-1
        for iIndex in range(0, len(_llsCommands)):
            try:
                oPopen = subprocess.Popen(
                    _llsCommands[iIndex],
                    cwd=_sWorkingDirectory,
                    stdin=subprocess.PIPE if iIndex > 0 else None,
                    stdout=subprocess.PIPE if iIndex < iIndex_last or _bRedirectStdOut else None,
                    stderr=subprocess.PIPE
                )
            except OSError as e:
                raise OSError(e.errno, str(e), iIndex_last-iIndex)
            (byStdOut, byStdErr) = oPopen.communicate(byStdOut)
            if not _bIgnoreReturnCode and oPopen.returncode != 0:
                raise OSError(oPopen.returncode, byStdErr.decode(sys.getfilesystemencoding()), iIndex_last-iIndex)
        if _bRedirectStdOut:
            if byStdOut:
                return byStdOut.decode(sys.getfilesystemencoding())
            else:
                return str()
        else:
            return None


    def perms(_mFile, _mUser, _mGroup, _mMode, _bTrace = False):
        """
        Change the given file permissions (user, group and mode)

        @param int|str _mFile   File descriptor or name
        @param int|str _mUser   User UID or name (or None to leave unchanged)
        @param int|str _mGroup  Group GID or name (or None to leave unchanged)
        @param int|str _mMode   Mode decimal bits or octal string (or None to leave unchanged)
        @param bool _bTrace     Print TRACE message to standard error

        @exception OSError  On file I/O error
        """

        # Change permisssions
        try:

            # ... user (name) <-> UID
            iUid = -1
            if _mUser is not None:
                if type(_mUser) is int:
                    iUid = _mUser
                else:
                    import pwd
                    iUid = pwd.getpwnam(_mUser).pw_uid

            # ... group (name) <-> GID
            iGid = -1
            if _mGroup is not None:
                if type(_mGroup) is int:
                    iGid = _mGroup
                else:
                    import grp
                    iGid = grp.getgrnam(_mGroup).gr_gid

            # ... mode
            iMode = -1
            if _mMode is not None:
                if type(_mMode) is int:
                    iMode = _mMode
                else:
                    iMode = int(_mMode, 8)

            # ... change owner
            if iUid >= 0 or iGid >= 0:
                if _bTrace: sys.stderr.write('TRACE[perms] Setting file owner: %s -> %d:%d\n' % (_mFile, iUid, iGid))
                if type(_mFile) is int:
                    os.fchown(_mFile, iUid, iGid)
                else:
                    os.chown(_mFile, iUid, iGid)

            # ... change mode
            if iMode >= 0:
                if _bTrace: sys.stderr.write('TRACE[perms] Setting file mode: %s -> %o\n' % (_mFile, iMode))
                if type(_mFile) is int:
                    os.fchmod(_mFile, iMode)
                else:
                    os.chmod(_mFile, iMode)

        except KeyError:
            raise OSError(errno.EINVAL, 'Invalid permissions (%s:%s)' % (_mUser, _mGroup))
        except ValueError:
            raise OSError(errno.EINVAL, 'Invalid permissions (%s)' % _mMode)


    def parseBool(_mBool):
        """
        Parse the given boolean string/value

        The following (lower-cased) string or values will resolve to True:
         - 'true' or 't'
         - 'yes' or 'y'
         - 'on'
         - '1'
         - bool = True
         - int != 0

        @param str|int|bool _mBool  Boolean string/value

        @return bool  Parsed boolean value

        @exception RuntimeError  On parse error
        """

        tBool = type(_mBool)
        if tBool is bool:
            return _mBool
        elif tBool is int:
            return _mBool != 0
        elif tBool is str:
            return _mBool.lower() in ['true', 'yes', 'on', '1']
        return False


    def parseList(_sList, _fCastFunction = None, _sItemSeparator = ','):
        """
        Parse the given list string

        A list string looks like:
          "value1[,...,valueN]"
        Value will be cast with the given function

        @param str _sList           List string
        @param str _fCastFunction   Cast function (ingored if None)
        @param str _sItemSeparator  Character separating each list item

        @return list  Parsed list

        @exception RuntimeError  On parse error
        """

        lmList = list()
        if _sList is None or not len(_sList):
            return lmList
        for mValue in _sList.split(_sItemSeparator):
            if not len(mValue):
                continue
            if _fCastFunction is None:
                mValue = mValue.strip()
            else:
                try:
                    mValue = _fCastFunction(mValue)
                except (NameError, ValueError, TypeError) as e:
                    raise RuntimeError('Failed to cast list value (%s)' % mValue)
            lmList.append(mValue)
        return lmList


    def parseDictionary(_sDictionary, _mDefaultValue = None, _fCastFunction = None, _sEntrySeparator = ',', _sAssignmentOperator = ':'):
        """
        Parse the given dictionary string

        A dictionary string looks like:
          "key1:value1[,key2,...,keyN:valueN]"
        The value may be omitted if a default value is given
        Also, value will be cast with the given function

        @param str _sDictionary           Dictionary string
        @param any _mDefaultValue         Default value for non-valued keys (erroneous if None)
        @param str _fCastFunction         Cast function (ingored if None)
        @param str _sEntrySeparator       Character separating each dictionary entries
        @param str _sAssignmentSeparator  Character assigning value to key

        @return dict  Parsed dictionary

        @exception RuntimeError  On parse error
        """

        dmDict = dict()
        if _sDictionary is None or not len(_sDictionary):
            return dmDict
        for sEntry in _sDictionary.split(_sEntrySeparator):
            if not len(sEntry):
                continue
            try:
                (sKey, mValue) = sEntry.split(_sAssignmentOperator)
            except ValueError as e:
                if _mDefaultValue is None:
                    raise RuntimeError('Dictionary entry has no value (%s)', sEntry)
                sKey = sEntry
                mValue = _mDefaultValue
            sKey = sKey.strip()
            if _fCastFunction is None:
                mValue = mValue.strip()
            else:
                try:
                    mValue = _fCastFunction(mValue)
                except (NameError, ValueError, TypeError) as e:
                    raise RuntimeError('Failed to cast dictionary value (%s)' % sEntry)
            dmDict[sKey] = mValue
        return dmDict
