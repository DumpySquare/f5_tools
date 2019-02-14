#!/usr/bin/python
# Issue bash/tmsh commands from api
# --  passing script args at execution
# Built on Python 3.7
# Created by Ben Gordon (F5 Consultant)
# Date:  10/18/2018
# additional features/thoughts:  add more error handling, check ip format?, parse more api response codes
#

import requests, json, argparse, getpass

# disable requests module warnings
from requests.packages.urllib3.exceptions import SNIMissingWarning, InsecurePlatformWarning, SubjectAltNameWarning, InsecureRequestWarning
requests.packages.urllib3.disable_warnings(SNIMissingWarning)
requests.packages.urllib3.disable_warnings(InsecurePlatformWarning)
requests.packages.urllib3.disable_warnings(SubjectAltNameWarning)
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# argument parser information
parser = argparse.ArgumentParser(description='This tool is used to send bash/tmsh commands to an f5 via api', epilog='By: Ben Gordon (bgordon@f5.com)')
parser.add_argument('-bigip', help='IP or hostname of BIG-IP Management or Self IP')
parser.add_argument('-user', help='username to use for authentication')
parser.add_argument('-cmd', help='bash or tmsh command to execute')
parser.add_argument('-interactive', action='store_true', help='prompts for necessary information if not passed as parameters')
args = parser.parse_args()	# assign the args from parser to a string


def main():
    print("---  f5 api to call local bash/tmsh commands ---")

    # if bigip not specified, prompt for bigip
    if not args.bigip:
        args.bigip = input('Enter BIGIP hostname or IP:  ')

    # if no username arg, prompt for username, if none, set default of admin
    if not args.user:
        args.user = input('Username [Enter] for admin:  ')
        if args.user == '':
            args.user = 'admin'

    # Prompt user for password
    passwd = getpass.getpass("Password for " + args.user + ":")

    # build base url with bigip ip
    BIGIP_URL_BASE = ('https://%s/mgmt/tm' % (args.bigip))

    # buid base rest call with username/password
    restbigip = buildbaserest(args.user, passwd)

    # start interactive loop
    if args.interactive:
        while args.cmd != 'quit':   # keep looping till quit
            print("-------------------------------------------------")
            print("--- bigip: %s, user: %s" % (args.bigip, args.user))
            print("--- Enter \"quit\" to exit")
            print("-------------------------------------------------")
            args.cmd = input('Enter bash/tmsh command to execute:  ')
            if args.cmd == "quit":
                quit()

            # call function to issue cmd
            issuecmd(BIGIP_URL_BASE, restbigip, args.cmd)

    else:
        # Make sure we have a command to send
        if not args.cmd:
            args.cmd = input('Command:  ')

        # call function to issue cmd
        issuecmd(BIGIP_URL_BASE, restbigip, args.cmd)


# REST resource for BIG-IP that all other requests will use
def buildbaserest(user, password):
    bigip = requests.session()
    bigip.auth = (user, password)
    bigip.verify = False    # do not verify certificate
    bigip.headers.update({'Content-Type': 'application/json'})
    return bigip

# build and issue command over api
def issuecmd(url, bigip, cmd):
    cmd = "-c '%s'" % cmd   # adding -c and formatting to make input easier
    payload = {}            # start json payload
    payload['command'] = 'run'
    payload['utilCmdArgs'] = cmd
    #print(json.dumps(payload, sort_keys=True, indent=4))   #shows json payload if needed
    fullurl = "%s/util/bash" % url  # set full url
    print ("Executing:  %s @ %s \n" % (payload, fullurl)) # display full payload and destination url
    response = bigip.post(fullurl, data=json.dumps(payload))    # post and assign response
    #print(response) # print response code
    #print(response.json())   # print raw response text(json)
    #print (json.loads(response))
    if response.status_code == requests.codes.ok:
        result = response.json().get('commandResult')   # return command result
        print(response) # print response code
        print(result)   # print command result
    elif response.status_code == requests.codes.unauthorized:
        print ("%s  Unauthorized - bad username/password?" % response)
    else:
        print ("Something went wrong:  %s - %s" % (response.status_code, response.raw))
        #print (response.content)
        #TODO: add full response information, not just response code, for troubleshooting purposes


if __name__ == "__main__":
    main()

