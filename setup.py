# -*- mode:python; tab-width:4; c-basic-offset:4; intent-tabs-mode:nil; -*-
# ex: filetype=python tabstop=4 softtabstop=4 shiftwidth=4 expandtab autoindent smartindent

# Modules
from distutils.core import setup
import os

# Setup
setup(
    name = 'KiSC',
    description = 'K.I.S.S. Cluster (KiSC)',
    long_description = \
"""
K.I.S.S. Cluster (KiSC) - with K.I.S.S. as in "Keep It Stupid Simple" - is
a utility that aims to simplify the life of administrators managing resources
accross a cluster of hosts.

The two main objectives of K.I.S.S. Cluster (KiSC) are:
 - provide a straight-forward way of defining cluster hosts and services,
   using simple INI file(s)
 - provide a no-daemon way of keeping track of hosts and services status,
   using runtime files stored on shared storage
""",
    version = os.getenv('VERSION'),
    author = 'Idiap Research Institute',
    author_email = 'http://www.idiap.ch',
    license = 'GPL-3',
    url = 'https://github.com/idiap/kisc',
    download_url = 'https://github.com/idiap/kisc',
    package_dir = { '': 'python' },
    packages = [ 'KiSC', 'KiSC.Cli', 'KiSC.Cluster', 'KiSC.Resource', 'KiSC.Runtime' ],
    scripts = [ 'kisc.py' ],
)
