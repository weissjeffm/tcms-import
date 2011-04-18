#!/usr/bin/python
#requires python-lxml, python-kerberos
from nitrate import NitrateKerbXmlrpc
import getopt, sys
from lxml import etree

url = 'https://tcms.engineering.redhat.com/xmlrpc/'
tree = None
n = None 
planid = None
build = None
productid = None
priorityid = None
product_version_id = None
def main():
    global planid,build,product_version_id,productid
    filename=""
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hp:f:b:v:t:", ["help", "url="])
        print(opts)
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

def create_run(planid, build, productid, product_version_id):
    return n.server.TestRun.create({"plan": planid, 
                                    "build": build, 
                                    "manager": n.get_me().get("id"),
                                    "product": productid,
                                    "summary": str(tree.xpath("//suite/@name")[0]), 
                                    "product_version": product_version_id}).get("run_id")
                            
def get_build(productid, build):
    b = n.server.Build.check_build(build,productid)
    print(b)
    if b.get("args"):
        b = n.server.Build.create({"product": productid, "name": build})
        print("Build doesn't exist in database, creating. \n%s" % str(b))
    return b.get("build_id")

def get_case(productid, categoryid, planid, alias, summary):
    try:
        tc = n.server.TestCase.filter({"alias": alias})[0]
        print(tc)
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
    global n,tree
    tree = etree.parse(f)
    n = NitrateKerbXmlrpc(url)
    print("Logged in as: " + str(n.get_me()))

    build = get_build(productid, build)
    run = create_run(planid, build, product_version_id)
    priorityid = n.server.TestCase.check_priority("P1").get("id")
    all_tests = tree.xpath("//test-method")
    for test in all_tests:
        name = test.attrib.get("name")
        clazz = tree.xpath("//class[/test-method[@name='%s']]" % name)[0].attrib.get("name")
        desc = test.attrib.get("description")
        ngstatus = test.attrib.get("status")
        sig = "%s.%s" % (clazz, name)
        statuses = {"PASS": "PASSED",
                    "FAIL": "FAILED",
                    "SKIP": "BLOCKED"}
        status = statuses[ngstatus]
        n.server.TestCaseRun.create({"run": run,
                                     "case": get_case(),
                                     "build": build,
                                     "case_run_status": status   
                })


def read(f):
    return etree.parse(f)
    
def groups_for_method(c,m):
    return tree.xpath("//group[method[@name='%s' and @class='%s']]/@name" % (m,c))

if __name__ == "__main__":
    main()
