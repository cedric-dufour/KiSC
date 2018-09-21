K.I.S.S. Cluster - Usage
========================

An example worth a thousand words: Configuration
------------------------------------------------

Start by configuring the cluster very base configuration; in `/etc/kisc.cfg`:

    ## K.I.S.S. Cluster (KiSC) configuration
    [KiSC]
    cache_dir=/var/cache/kisc
    local_runtime_dir=/var/run/kisk
    global_runtime_dir=/kisc/run
    
    ## Bootstrap (host startup) resources
    #  (automatically started when parsing this file)
    
    # LAN health check
    [ping-lan]
    TYPE=health_ping
    address=192.16.0.1
    
    # Shared storage
    [mount-kisc]
    TYPE=storage_mount
    fstype=nfs
    device=nfs-server.example.org:/kisc
    mountpoint=/kisc
    options=tcp,rw,hard,intr
    
    
    ## Other resources
    
    # Additional bootstrap resources (automatically started when host is started)
    [include-bootstrap]
    TYPE=include
    BOOTSTRAP=yes
    file=/kisc/shared/bootstrap/bootstrap.cfg
    
    # Cluster hosts definition
    [include-hosts]
    TYPE=include
    BOOTSTRAP=yes
    file=/kisc/shared/bootstrap/hosts.cfg
    
    # Cluster services
    [include-services]
    TYPE=include
    file=/kisc/shared/services.cfg


Configure additional bootstrap resources; in (shared storage) `/kisc/shared/bootstrap/bootstrap.cfg`:

    ## Network configuration
    
    # DMZ VLAN
    [vlan-dmz]
    TYPE=network_vlan
    name=vlan2
    vlan=2
    device=eth0
    
    # DMZ bridge (to attach virtual machines)
    [br-dmz]
    TYPE=network_bridge
    name=br1
    devices=vlan2
    
    ## Storage configuration

    # DMZ storage
    [mount-dmz]
    TYPE=storage_mount
    fstype=nfs
    device=nfs-server.example.org:/kisc
    mountpoint=/kisc/shared/images/dmz
    options=tcp,rw,hard,intr
    


Configure cluster hosts; in (shared storage) `/kisc/shared/bootstrap/hosts.cfg`:

    ## Cluster hosts
    
    # Host N.1
    [node01]
    TYPE=cluster_host
    hostname=node01.example.org
    CONSUMABLES=CPU:4,RAM:4096
    
    # Host N.2
    [node02]
    TYPE=cluster_host
    hostname=node02.example.org
    CONSUMABLES=CPU:4,RAM:4096
    
    # Host N.3
    [node03]
    TYPE=cluster_host
    hostname=node03.example.org
    CONSUMABLES=CPU:2,RAM:2048
    
    # Hostgroup
    [nodes-large]
    TYPE=cluster_hostgroup
    hosts=node01,node02


Configure cluster services; in (shared storage) `/kisc/shared/services.cfg`:

    ## Cluster services
    
    # Virtual machine N.1
    [VM1]
    TYPE=service_libvirt
    name=VM1
    config_file=/kisc/shared/libvirt/VM1.xml
    mac_address=02:00:C0:A8:01:65
    CONSUMES=CPU:1,RAM:1024
    
    [VM2]
    TYPE=service_libvirt
    name=VM2
    config_file=/kisc/shared/libvirt/VM2.xml
    mac_address=02:00:C0:A8:01:66
    CONSUMES=CPU:4,RAM:2048
    HOSTS=@nodes-large


Thanks to the "caching" feature and cluster variables substitution,
your `/kisc/shared/libvirt/*.xml` can be much simplified and templated:

    <domain type='kvm'>
      <name>%{SELF.name}</name>
      <memory>%{SELF.CONSUMES[RAM]|int|mul(1024)}</memory>
      <vcpu>%{SELF.CONSUMES[CPU]}</vcpu>
      <devices>
        <emulator>/usr/bin/kvm</emulator>
        <disk type='file' device='disk'>
          <driver name='qemu' type='raw'/>
          <source file='%{mount-dmz.mountpoint}/%{SELF.name}.raw'/>
          <target dev='vda' bus='virtio'/>
        </disk>
        <interface type='bridge'>
          <mac address='%{SELF.mac_address}'/>
          <source bridge='%{br-dmz.name}'/>
          <model type='virtio'/>
        </interface>
        <!-- etc. -->
      </devices>
      <!-- etc. -->
    </domain>


An example worth a thousand words (cont'd): Commands
----------------------------------------------------

Starting a cluster node and its bootstrap resources:

    CLI# ssh node01.example.org kisc host start


Starting a service on a cluster node:

    CLI# ssh node01.example.org kisc resource start VM1


Query a service configuration and status (from any cluster node)

    CLI# ssh node02.example.org kisc resource status VM1
    [VM1]
    TYPE=service_libvirt
    name=VM1
    config_file=/kisc/libvirt/VM1.xml
    mac_address=02:00:C0:A8:00:65
    CONSUMES=CPU:1,RAM:1024
    $HOSTS=node01
    $STATUS=Started


Query a host configuration and status (from any cluster node)

    CLI# ssh node02.example.org kisc host status --host node01
    [node01]
    TYPE=cluster_host
    CONSUMABLES=CPU:4,RAM:4096
    hostname=node01.example.org
    $BOOTSTRAP=ping-lan,mount-kisc,vlan-dmz,br-dmz
    $CONSUMABLES_USED=CPU:1,RAM:1024
    $CONSUMABLES_FREE=CPU:3,RAM:3072
    $RESOURCES=VM1
    $STATUS=Started


Further examples
----------------

Please browse the EXAMPLES directory.


Further help, commands and options
----------------------------------

As simple as it gets:

    CLI# kisc --help

