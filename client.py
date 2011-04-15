#!/usr/bin/python
from nitrate import NitrateKerbXmlrpc
import getopt, sys


url = 'https://tcms.engineering.redhat.com/xmlrpc/'
filename = ""

def main():

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hp:f:", ["help", "url="])
        print(opts)
    except getopt.GetoptError, err:
        # print help information and exit:
        print str(err) # will print something like "option -a not recognized"
        usage()
        sys.exit(2)

    port = 8001 #default port

    for o, a in opts:
        if o in ("-u", "--url"): 
            url = a
        elif o in ("-f"):
            filename = a
        elif o in ("-h", "--help"):
            usage()
            sys.exit()
        else:
            assert False, "unhandled option"

    upload_all()

def upload_all():
    n = NitrateKerbXmlrpc(url)
    print("Logged in as: " + str(n.get_me()))


    

if __name__ == "__main__":
    main()
