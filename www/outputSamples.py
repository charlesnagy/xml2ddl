import re, sys
sys.path += ['../']
import xml2ddl, diffxml2ddl

def doCreate(strDbms, strFilename):
    print '\tpython xml2ddl.py --dbms %s %s' % (strDbms, strFilename)
    print
    
    cd = xml2ddl.Xml2Ddl()
    cd.setDbms(strDbms)
    xml = xml2ddl.readMergeDict(strFilename)
    results = cd.createTables(xml)
    for result in results:
        print "\t%s;" % (result[1].replace('\t', '\t\t'))

    print
    
def doDiff(strDbms, strNewFile, strOldFile):
    print '\tpython diffxml2ddl.py --dbms %s %s %s' % (strDbms, strNewFile, strOldFile)
    print
    
    fdc = diffxml2ddl.FindChanges()
    fdc.setDbms(strDbms)
    results = fdc.diffFiles(strOldFile, strNewFile)
    for result in results:
        print "\t%s;" % (result[1].replace('\t', '\t\t'))

    print

doCreate('postgres', 'schema1.xml')

doCreate('firebird', 'schema1.xml')

doDiff('postgres', 'schema1.xml', 'schema2.xml')

doDiff('postgres7', 'schema1.xml', 'schema2.xml')

