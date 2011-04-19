#!/usr/bin/python
#requires python-lxml, python-kerberos
from nitrate import NitrateKerbXmlrpc
import getopt, sys
from lxml import etree

url = 'https://tcms.engineering.redhat.com/xmlrpc/'

def main():
    filename=""
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hp:f:b:v:t:", ["help", "url="])
        #print(opts)
    except getopt.GetoptError, err:
        # print help information and exit:
        print str(err) # will print something like "option -a not recognized"
        usage()
        sys.exit(2)

    for o, a in opts:
        if o in ("-u", "--url"): 
            url = a
        elif o in ("-f"):
            filename = a
        elif o in ("-t"):
            planid = a
        elif o in ("-b"):
            build = a
        elif o in ("-p"):
            productid = a
        elif o in ("-v"):
            product_version_id = a
        elif o in ("-h", "--help"):
            usage()
            sys.exit()
        else:
            assert False, "unhandled option"

    upload_all(filename, planid, build, productid, product_version_id)

def usage():
    print("tcms-import.py\n-f [testng result xml filename]\n-t [test plan id]\n-b [build name]\n-p [product id]\n-v [product version id]\n\nImports into tcms all the results from a testng result file.  The various IDs can be gotten from the TCMS web interface (the easiest way is just to hover over links to those resources, the ID is part of the link URL).  \n\nYou must have a valid kerberos ticket (by running kinit) before running this script.  \n\nThis script depends on these packages: python-lxml, python-kerberos.")
                            
def get_build(n, productid, build):
    b = n.server.Build.check_build(build,productid)
    #print(b)
    if b.get("args"):
        b = n.server.Build.create({"product": productid, "name": build})
        print("Build doesn't exist in database, creating. \n%s" % str(b))
    return b.get("build_id")

def get_case(n, productid, categoryid, planid, priorityid, alias, summary):
    print("using pri %s sum %s alias %s " % (priorityid, summary, alias))
    try:
        tc = n.server.TestCase.filter({"alias": alias})[0]
        #print(tc)
    except IndexError:
        tc = n.server.TestCase.create({"product": productid, 
                                       "category": categoryid,
                                       "priority": priorityid,
                                       "summary": summary,
                                       "plan": planid,
                                       "alias": alias,
                                       "is_automated": 1})
        print("Testcase doesn't exist in database, creating. \n%s" % str(tc))
    return tc.get("case_id")

def upload_all(f, planid, build, productid, product_version_id):
    #global n,tree,priorityid,categoryid
    tree = etree.parse(f)
    n = NitrateKerbXmlrpc(url)
    #print("Logged in as: " + str(n.get_me()))

    build = get_build(n, productid, build)
    run = n.server.TestRun.create({"plan": planid, 
                                    "build": build, 
                                    "manager": n.get_me().get("id"),
                                    "product": productid,
                                    "summary": str(tree.xpath("//suite/@name")[0]), 
                                    "product_version": product_version_id}).get("run_id")

    priorityid = n.server.TestCase.check_priority("P1").get("id")
    categoryid = n.server.Product.check_category("--default--", productid).get("id")
    all_tests = filter(lambda tc: tc.attrib.get("is-config") == None, tree.xpath("//test-method"))

    statuses = {"PASS": n.server.TestCaseRun.check_case_run_status("PASSED").get("id"),
                "FAIL": n.server.TestCaseRun.check_case_run_status("FAILED").get("id"), 
                "SKIP": n.server.TestCaseRun.check_case_run_status("BLOCKED").get("id")}

    for test in all_tests:
        name = test.attrib.get("name")
        methodsig = test.attrib.get("signature")
        
        #print("testname is %s" % name)
        clazz = tree.xpath("//class[test-method[@name='%s']]" % name)[0].attrib.get("name")
        ngstatus = test.attrib.get("status")
        sig = "%s.%s" % (clazz, methodsig.rsplit("(")[0])
        desc = test.attrib.get("description") or sig
        status = statuses[ngstatus]
        exceptions = tree.xpath("//test-method[@name='%s']//full-stacktrace" % name)
        if len(exceptions) > 0:
            notes = exceptions[0].text
        else:
            notes = ""
        n.server.TestCaseRun.create({"run": run,
                                     "case": get_case(n, productid, categoryid, planid, priorityid, sig, desc),
                                     "build": build,
                                     "case_run_status": status,
                                     "notes": notes})

    print("Uploaded %d test results." % len(all_tests))
    
def groups_for_method(c,m):
    return tree.xpath("//group[method[@name='%s' and @class='%s']]/@name" % (m,c))

if __name__ == "__main__":
    main()
