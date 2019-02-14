#!/usr/bin/python

# Title:    Import F5 BIG-IQ devices to Ansible inventory
# This script will pull back a list of device names and mgmt. IP addresses via API from a BIG-IQ
#   and create an Ansible inventory file

# Built on Python 2.6.6/2.7.15 for BIGIQ 6.1, TMOS v13
# Created by Ben Gordon (F5 Consultant)
# Date:  01/29/2019
# additional features/thoughts:  Need to setup cluster names (on bigiq and add field via api call)
#     to allow HA sync for expanded functionality


import requests
import argparse
import datetime
# import urllib3

# disable requests module warnings
from requests.packages.urllib3.exceptions import SNIMissingWarning
from requests.packages.urllib3.exceptions import InsecurePlatformWarning
from requests.packages.urllib3.exceptions import SubjectAltNameWarning
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(SNIMissingWarning)
requests.packages.urllib3.disable_warnings(InsecurePlatformWarning)
requests.packages.urllib3.disable_warnings(SubjectAltNameWarning)
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# argument parser information
parser = argparse.ArgumentParser(description='This tool is used to Ansible inventory INI file from BIG-IQ device list'
, epilog='By: Ben Gordon (bgordon@f5.com)')
parser.add_argument('-bigiq', help='IP or hostname of BIG-IQ Management or Self IP')
parser.add_argument('-user', help='username to use for authentication')
parser.add_argument('-destfile', help='output file <location>/<name>')
# parser.add_argument('-interactive', action='store_true', help='prompts for necessary information if not passed as parameters')
args = parser.parse_args()  # assign the args from parser to a string


def main():
    print("\n---  Calling API to get BIG-IQ device for Ansible inventory  ---\n")
    args.bigiq = "10.10.10.10"
    args.user = "admin"
    args.destfile = "bigiq_inv.ini"
    # TODO:  include arg for device groups?
    passwd = "niftypassowrd"

    # build base url with bigip ip
    BIGIQ_URL_BASE = ('https://%s/mgmt/' % args.bigiq)

    # buid base rest call with username/password
    restbigip = buildbaserest(args.user, passwd)

    # call function to issue api
    issuecmd(BIGIQ_URL_BASE, restbigip)


def buildbaserest(user, password):
    bigiq = requests.session()
    bigiq.auth = (user, password)
    bigiq.verify = False  # do not verify certificate
    bigiq.headers.update({'Content-Type': 'application/json'})
    return bigiq


def issuecmd(url, bigiq):
    # url for bigiq device list
    bigiqdevicesurl = "shared/resolver/device-groups/cm-bigip-allDevices/devices"

    # filter to only return hostname and managment IP
    selectfilter = "?$select=hostname,managementAddress"

    # Grab current time for logging in inventory file
    now = datetime.datetime.now()

    fullurl = "%s%s%s" % (url, bigiqdevicesurl, selectfilter)  # build full url
    print ("Executing:  %s \n" % fullurl)  # display full destination url
    response = bigiq.get(fullurl)  # post and assign response

    if response.status_code == requests.codes.ok:
        result = response.json()  # return command result to array
        print(response)  # print response code for fyi

        # open the destination file
        invfile = open("%s" % args.destfile, "w")

        # write some header stuff to let people know what's going on
        invfile.write("#    imported %s devices from bigiq:  %s\n" % (len(result['items']), args.bigiq))
        invfile.write("#    import date:  %s\n\n" % str(now))

        # set ansible device group
        invfile.write('[bigiq_devices]\n')

        # loop through items in array and write hostname and managementAddress to file in a specific format
        for device in result['items']:
            # print "%s\t\tansible_host=%s" % (device['hostname'], device['managementAddress'])
            invfile.write("%s\t\tansible_host=%s\n" % (device['hostname'], device['managementAddress']))

        # close the file
        invfile.close()

    # if password is wrong, following error
    elif response.status_code == requests.codes.unauthorized:
        print ("%s  Unauthorized - bad username/password?" % response)
    else:

        # something other than password went wrong - exit with https response code and raw response
        print ("Something went wrong:  %s - %s" % (response.status_code, response.raw))
        # print (response.content)   #print raw response content if needed
        # TODO: add full response information, not just response code, for troubleshooting purposes


if __name__ == "__main__":
    main()
