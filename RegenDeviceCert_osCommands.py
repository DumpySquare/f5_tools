#!/usr/bin/python

# F5 ReGen Device Cert Self Signed
# This script uses hostname to update device cert
# to be run on local bigip or pushed via another tool like bigiq/ansible
#
# Built on Python 2.6.6 for BIGIQ TMOS v13
# Created by Ben Gordon (F5 Consultant)
# Date:  2/14/2019
# additional features/thoughts:
#
#   K6353: Updating a self-signed SSL device certificate on a BIG-IP system
#       https://support.f5.com/csp/article/K6353
#
# this does not touch the DSC certs, for HA, in the following locations:
#   - /config/ssl/ssl.crt/dtdi.crt
#   - /config/ssl/ssl.crt/dtdi.key

import os
import commands
import time
from socket import gethostname

days = 3650  # 10 years
C = "US"  # Country
# ST = "TN"   # State		# decided not to use
# L = "Nashville" # City/Locality	# decided not to use
O = "f5"  # Organization
OU = "IT"  # Division
CN = gethostname()  # Sets Common Name as hostname
key = "rsa:2048"
keyname = "server.key"  # default for now
certname = "server.crt"   # default for now
guicertlocation = "/config/httpd/conf/ssl.crt/"
guikeylocation = "/config/httpd/conf/ssl.key/"
fullcert = "%s%s" % (guicertlocation, certname)
fullkey = "%s%s" % (guikeylocation, keyname)
liclocation = "/config/bigip.license"


def main():
    # Check for default cert/key and license files
    # to confirm this is actually a bigip
    if not (os.path.exists(fullcert) or os.path.exists(fullkey) or os.path.exists(liclocation)):
        sys.exit(' *****  Not a BIG-IP, EXITING!!!  ***** ')

    print ("\n---   Updating Device Certificate to hostname   ---")
    print ("    hostname: %s\n" % CN)
    backuporiginalcertkey(fullkey, fullcert)
    gencert(C, O, OU, CN, days, key, fullkey, fullcert)
    confirmcertkeymatch(fullkey, fullcert)
    cert2trust(fullcert)
    restarthttpd()
    saveconfig()



def backuporiginalcertkey(fullkey, fullcert):
    print("---  Backing up original cert/key  ---")

    oldkey = ("%s.old" % fullkey)
    oldcert = ("%s.old" % fullcert)

    cmd = "cp %s %s" % (fullkey, oldkey)
    print ("    Executing:  %s" % cmd)
    os.system(cmd)

    cmd = "cp %s %s" % (fullcert, oldcert)
    print ("    Executing:  %s" % cmd)
    os.system(cmd)

    print ("\n")


def gencert(C, O, OU, CN, days, key, fullkey, fullcert):
    # broke the followin logic into multiple lines to make it easier to read
    # build the subject information string
    subj = "/C=%s/O=%s/OU=%s/CN=%s" % (C, O, OU, CN)
    # build the full command
    gencert = "openssl req -x509 -nodes -days %s -newkey %s -subj '%s' -keyout %s -out %s" \
              % (days, key, subj, fullkey, fullcert)
    # Generate the cert/key
    # this will replace the current files at fullkey/fullcert
    print ("---   generating cert/key   ---")
    print ("Executing:  %s" % gencert)
    os.system(gencert)
    time.sleep(1)
    print ("\n")


def confirmcertkeymatch(key, cert):
    # Get mod of cert/key and convert to md5 hash
    certmd5 = commands.getoutput("openssl x509 -noout -modulus -in %s | openssl md5" % cert)
    keymd5 = commands.getoutput("openssl rsa -noout -modulus -in %s | openssl md5" % key)

    # strip off leading junk
    certmd5 = certmd5.lstrip("(stdin)=")
    keymd5 = keymd5.lstrip("(stdin)=")

    print ("---   Confirming cert/key match   ---")
    print ("    Cert md5:  %s" % certmd5)
    print ("    Key md5:  %s" % keymd5)

    # compare cert/key md5 hash to confirm they are a match
    if certmd5 == keymd5:
        print ("    Cert/Key MATCH!!!\n")
        return True
    else:
        print ("    Cert/Key does not match!!!\n")
        return False


def cert2trust(fullcert):
    # add new cert to trusted cert stores
    print("---   add new cert to trusted cert stores   ---")

    # add to the list of certs an LTM should trust (includes self)
    cmd = "cat %s >> /config/big3d/client.crt" % (fullcert)
    print ("    Executing:  %s" % cmd)
    os.system(cmd)

    # add to the list of certs a GTM should trust (includes self)
    cmd = "cat %s >> /config/gtm/server.crt" % (fullcert)
    print("    Executing:  %s" % cmd)
    os.system(cmd)
    print ("")


def restarthttpd():
    # restart httpd service to use the new cert/key specified
    cmd = "tmsh restart sys service httpd"
    print ("---   restarting gui httpd daemon   ---")
    print ("    Executing:  %s" % cmd)
    os.system(cmd)


def saveconfig():
    # save sys config
    cmd = "tmsh save sys config"
    print ("\nExecuting:  %s" % cmd)
    os.system(cmd)


if __name__ == "__main__":
    main()
