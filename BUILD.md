K.I.S.S. Cluster - Build instructions
=====================================

1. [MUST] Obtain the source tarball:

      CLI# tar -xjf kisc-source-@version@.tar.bz2
      CLI# cd kisc-source-@version@

2. [MAY] (Re-)build the source tarball:

      CLI# ./debian/rules build-source-tarball
      CLI# ls -al ../kisc-source-@version@.tar.bz2

3. [MAY] Build the installation (release) tarball:

      CLI# ./debian/rules build-install-tarball
      CLI# ls -al ../kisc-@version@.tar.bz2

4. [MAY] Build the debian packages:

      CLI# debuild -us -uc -b
      CLI# ls -al ../kisc*@version@*.deb

5. [MAY] Build the debian source package:

      CLI# debuild -I'.git*' -I'*.pyc' -us -uc -S
      CLI# ls -al ../kisc_@version@.dsc ../kisc_@version@.tar.gz

OR

6. [SHOULD] Do it all with a single command

      CLI# ./debian/rules release

