#!/usr/bin/env python

import os
import json
import subprocess

#
# Volume service PoC. Designed to be run from a priv container on a host. #
#

def devNumbers(device):
     numbers = os.popen('stat --format "0x%t 0x%T" ' + device).read()
     return os.popen('printf "%d %d" ' + numbers).read()

def targetPid(hostname): 
     return os.popen("docker inspect --format {{.State.Pid}} %s" % hostname).read().strip()

# Creates a device in a target container. the device exists on the host.
def mountDevice(targetHostname, device):
     pid = targetPid(targetHostname)
     dnumbers = devNumbers(device)
     return os.popen("nsenter --mount=/media/host/proc/%s/ns/mnt -- mknod --mode 0600 %s b %s" % (pid, device, dnumbers)).read()


# In a bind mount - the hostDir is relative to the mount point of device. 
# so say you have /dev/xvdb -> /mnt, and you want /mnt/foo in the host as /boo - you would call
# bindMount("foo", ..., /dev/xvdb, "/boo")
# SEE doBindMount below for the equivalent of what you do on the docker cli
def bindMount(hostDir, targetHostname, device, targetHostPath):
     mountDevice(targetHostname, device)
     pid = targetPid(targetHostname)
     os.popen("nsenter --mount=/media/host/proc/%s/ns/mnt -- mkdir -p /tmpmnt" % pid).read()
     os.popen("nsenter --mount=/media/host/proc/%s/ns/mnt -- mount %s /tmpmnt" % (pid, device)).read()
     os.popen("nsenter --mount=/media/host/proc/%s/ns/mnt -- mkdir -p %s" % (pid, targetHostPath)).read()
     os.popen("nsenter --mount=/media/host/proc/%s/ns/mnt -- mount -o bind /tmpmnt/%s %s" % (pid, hostDir, targetHostPath)).read()
     os.popen("nsenter --mount=/media/host/proc/%s/ns/mnt -- umount /tmpmnt" % pid).read()
     os.popen("nsenter --mount=/media/host/proc/%s/ns/mnt -- rmdir /tmpmnt" % pid).read()

def mountPoint(hostPath):
     return os.popen("nsenter --mount=/media/host/proc/1/ns/mnt -- df -P %s | tail -n 1 | awk '{print $6}'" % hostPath).read().strip()

def getDevice(mountPoint):
     return os.popen("nsenter --mount=/media/host/proc/1/ns/mnt -- cat /proc/mounts | grep %s | awk '{print $1}' | head -n 1" % mountPoint).read().strip()
     
# this actually works out the device and the mount point via "magic" 
# bind mount the hostPath to the targetPath for the target container (it looks up its pid from the hostname)
def doBindMount(hostPath, targetPath, targetHostname):
     mtPnt = mountPoint(hostPath)
     device = getDevice(mtPnt)
     hostDir = hostPath.strip(mtPnt + "/")
     bindMount(hostDir, targetHostname, device, targetPath)
