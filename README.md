K.I.S.S. Cluster
================

K.I.S.S. Cluster (KiSC) - with K.I.S.S. as in "Keep It Stupid Simple" - is
a utility that aims to simplify the life of administrators managing resources
accross a cluster of hosts.

The two main objectives of K.I.S.S. Cluster (KiSC) are:

* provide a straight-forward way of defining cluster hosts and services,
  using simple INI file(s)

* provide a no-daemon way of keeping track of hosts and services status,
  using runtime files stored on shared storage


What K.I.S.S. Cluster (KiSC) DOES
---------------------------------

Bottom-line, K.I.S.S. Cluster (KiSC) provides a simple and easy way to:

* manage a central configuration repository on shared storage
 
* make sure cluster hosts have all dependencies (network, storage, health
  checks, etc.) properly bootstrapped before providing services
 
* start, query and stop cluster services in a unified, consolidated way


What K.I.S.S. Cluster (KiSC) does NOT
-------------------------------------

* It does not handle remote command execution!  
  K.I.S.S.! Why try to do what ssh [1] - potentially along pdsh [2] and genders [3] -
  already does so well?

* It does not handle concurrency (administrators launching simultaneous commands)!  
  K.I.S.S.!

* It does not handle high-availability!  
  K.I.S.S.! But it does integrate elegantly with pacemaker [4]!

[1] https://www.openssh.com/  
[2] https://github.com/chaos/pdsh/  
[3] https://github.com/chaos/genders/  
[4] https://clusterlabs.org/


Build and usage
---------------

Please refer to the BUILD and USAGE files.

