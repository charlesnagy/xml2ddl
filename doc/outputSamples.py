import re, sys
sys.path += ['../']
import xml2ddl.xml2ddl
import xml2ddl.diffxml2ddl
import xml2ddl.ddlInterface
from xml2ddl.ddlInterface import g_dbTypes
import glob
import codecs
from xml.dom.minidom import parse, parseString

class OutputSamples:
    def __init__(self):
        self.allDbmss = g_dbTypes[:]
        self.strTestDir = r'../tests/testfiles/test*.xml'
        self.strOutfile = 'testdetails.html'
        
    def doCreate(self, strDbms, strFilename):
        print '\tpython xml2ddl.py --dbms %s %s' % (strDbms, strFilename)
        print
        
        cd = xml2ddl.Xml2Ddl()
        cd.setDbms(strDbms)
        xml = xml2ddl.readMergeDict(strFilename)
        results = cd.createTables(xml)
        for result in results:
            print "\t%s;" % (result[1].replace('\t', '\t\t'))
    
        print
        
    def doDiff(self, strDbms, strNewFile, strOldFile):
        print '\tpython diffxml2ddl.py --dbms %s %s %s' % (strDbms, strNewFile, strOldFile)
        print
        
        fdc = diffxml2ddl.FindChanges()
        fdc.setDbms(strDbms)
        results = fdc.diffFiles(strOldFile, strNewFile)
        for result in results:
            print "\t%s;" % (result[1].replace('\t', '\t\t'))
    
        print
    
    def writeHeader(self, fo):
        fo.write('<html>\n')
        fo.write('<head>\n')
        fo.write('<link rel="stylesheet" href="default.css" type="text/css" />\n')
        fo.write('</head>\n')
        fo.write('<body>\n')
        fo.write('<div class="document" id="xml-to-ddl">\n')
        fo.write('<h2>Introduction</h2>\n')
        fo.write('<div class="intro">\n')
        fo.write(
    """
    The following is a list of examples of diffxml2ddl's output.
    The XML on the left is the database schema before hand, and the XML on the right
    is what we want to get to.
    Underneath them is the list of SQL statements required to get from the Before to the After
    for each type of DBMS supported.<br/>
    
    The output comes directly from the test files which are used to unit test xml2ddl.
    
    """)
        fo.write('</head>\n')
    
    def writeLeftRight(self, fo, before, after):
        fo.write('<table width="100%" class="beforeafter">\n')
        fo.write('<tr>\n')
        fo.write('<th>Before</th>')
        fo.write('<th class="after">After</th>')
        fo.write('</tr>\n')
        fo.write('<tr>\n')
        
        fo.write('<td"><div class="xml">\n')
        fo.write(self.prettyXml(before.toxml()))
        fo.write('</div></td>\n')
        
        fo.write('<td class="after"><div class="xml">\n')
        fo.write(self.prettyXml(after.toxml()))
        fo.write('</div></td>\n')
        fo.write('</tr>\n')
        
        fo.write('</table>\n')
    
    def writeDdls(self, fo, ddls):
        remainingDbms = self.allDbmss[:]
        for ddl in ddls:
            strDmss = ddl.getAttribute('dbms')
            for dbms in strDmss.split(','):
                if dbms:
                    if dbms in remainingDbms:
                        remainingDbms.remove(dbms)
        
        for ddl in ddls:
            self.writeDdl(fo, ddl, remainingDbms)
    
    def writeDdl(self, fo, ddls, remainingDbms):
        fo.write('<table class="ddls" width="100%">\n')
        fo.write('<tr>\n')
        strDbms = ddls.getAttribute('dbms')
        strFails = ddls.getAttribute('fails')
        strDesc = ddls.getAttribute('desc') 
        if len(strDbms) == 0:
            strDbms = ', '.join(remainingDbms)
        
        if len(strFails) > 0:
            strDbms += ' <span class="warning">%s</span>' % ('Warning: Fails')
        
        fo.write('<th align="left">DBMS: %s</th>' % (strDbms))
        fo.write('</tr>\n')
        
        if len(strDesc) > 0:
            fo.write('<tr>\n')
            fo.write('<td>Note: <em>%s</em></td>' % (strDesc))
            fo.write('</tr>\n')
            
        for ddl in ddls.getElementsByTagName('ddl'):
            fo.write('<tr>\n')
            fo.write('<td>%s;</td>' % (self.prettyDdl(ddl.firstChild.nodeValue)))
            fo.write('</tr>\n')
            
        fo.write('</table>\n')
    
    def writeFooter(self, fo):
        fo.write('</div>\n')
        fo.write('</body>\n')
        fo.write('</html>\n')
        
    def createDoc(self, ):
        self.fo = codecs.open(self.strOutfile, "w", 'ISO-8859-1')
        self.writeHeader(self.fo)
        
        self.doIndex()
        self.doSupportGrid()
        
        self.doTestDetails()
        
        self.writeFooter(self.fo)
        self.fo.close()
        
        print "Created '%s'" % (self.strOutfile)
    
    def doIndex(self):
        files = glob.glob(self.strTestDir)
        nTestNumber = 0
        
        self.fo.write('<table>')
        self.fo.write('<td></td><td><h2>Index</h2></td>\n')
        for testFilename in files:
            nTestNumber += 1
            doc = parse(testFilename)
            strDesc = doc.getElementsByTagName('test')[0].getAttribute('title')
            
            self.fo.write('<tr>')
            self.fo.write('<td align="right">%d -</td>' % (nTestNumber))
            self.fo.write('<td><a href="%s" class="ddltitle">%s</a></td>\n' % ("#_%d" % (nTestNumber), strDesc))
            self.fo.write('</tr>')
            
            doc.unlink()
            
        self.fo.write('</table>')
        if nTestNumber == 0:
            print "No files found for '%s'" % (self.strTestDir)

    def doSupportGrid(self):
        files = glob.glob(self.strTestDir)
        nTestNumber = 0
        
        self.fo.write('<table style="border-collapse:collapse;borderspacing:0">')
        self.fo.write('<td></td><td><h2>Index</h2></td>\n')
        self.fo.write('<tr>')
        self.fo.write('<td style="text-align:right">Description</td>')
        for dbms in self.allDbmss:
            self.fo.write('<td style="text-align:center;width:8ex">%s</td>' % (dbms.capitalize()))
        self.fo.write('</tr>')
        
        for testFilename in files:
            nTestNumber += 1
            doc = parse(testFilename)
            strDesc = doc.getElementsByTagName('test')[0].getAttribute('title')
            
            self.fo.write('<tr>')
            self.fo.write('<td style="text-align:right"><a href="%s" class="ddltitle">%s</a></td>\n' % ("#_%d" % (nTestNumber), strDesc))

            strSupportTxt = '<img alt="yes" src="yes.gif"/>'
            strFailsTxt = '<img alt="no" src="no.gif"/>'
            dbmsSupport = {}
            for dbms in self.allDbmss:
                dbmsSupport[dbms] = strSupportTxt 
                
            docDdls = doc.getElementsByTagName('ddls')
            for ddl in docDdls:
                strDmss = ddl.getAttribute('dbms')
                strFails = ddl.getAttribute('fails')
                for dbms in strDmss.split(','):
                    if dbms:
                        if strFails.lower() == 'true':
                            dbmsSupport[dbms] = strFailsTxt
            
            for dbms in self.allDbmss:
                self.fo.write('<td style="border:1px solid black;text-align:center">%s</td>' % (dbmsSupport[dbms]))
            self.fo.write('</tr>')
            
            doc.unlink()
            
        self.fo.write('</table>')

    def doTestDetails(self):
        files = glob.glob(self.strTestDir)
        nTestNumber = 0
        for testFilename in files:
            nTestNumber += 1
            doc = parse(testFilename)
    
            strDesc = doc.getElementsByTagName('test')[0].getAttribute('title')
            
            self.fo.write('<div id="%s" class="ddltitle">%d %s</div>\n' % ("_%d" % (nTestNumber), nTestNumber, strDesc))
            self.fo.write('<small>%s</small>\n' % (testFilename))
            
            docBefore = doc.getElementsByTagName('before')[0].firstChild.nextSibling
            
            docAfter = doc.getElementsByTagName('after')[0].firstChild.nextSibling
            
            self.writeLeftRight(self.fo, docBefore, docAfter)
            
            docDdls = doc.getElementsByTagName('ddls')
            
            self.writeDdls(self.fo, docDdls)
            
            doc.unlink()
        
        
    def prettyXml(self, strText):
        re_special_lt = re.compile(r'<')
        strText = re_special_lt.sub('&lt;', strText)
    
        re_first_spaces = re.compile(r'\n    ')
        strText = re_first_spaces.sub('<br/>', strText)
        
    
        re_reduce_indent = re.compile(r'    ')
        strText = re_reduce_indent.sub('&nbsp;&nbsp;&nbsp;&nbsp;', strText)
        #~ re_linefeeds = re.compile(r'\n')
        #~ strText = re_linefeeds.sub('<br/>', strText)
        
        #~ re_indents = re.compile(r'(\t|    )')
    
        re_quoted = re.compile(r'([a-zA-Z_]*)="([^"]+)"')
        strText = re_quoted.sub(r'<span class="attrib">\1</span>="\2"', strText)
        
        re_tags = re.compile(r'(&lt;[/]?[a-z]+[> ])')
        strText = re_tags.sub(r'<span class="tags">\1</span>', strText)
        
        return strText
    
    def prettyDdl(self, strText):
        re_first_spaces = re.compile(r'\n')
        strText = re_first_spaces.sub('<br/>', strText)
        
        cd = xml2ddl.ddlInterface.createDdlInterface('firebird') # Firebird has the most keywords

        re_keywords = re.compile(r'\b(%s)\b' % ('|'.join(cd.params['keywords'])), re.IGNORECASE)
        strText = re_keywords.sub(r'<span class="keyword">\1</span>', strText)
    
        re_reduce_indent = re.compile(r'    ')
        strText = re_reduce_indent.sub('&nbsp;&nbsp;&nbsp;&nbsp;', strText)
        
        return strText

#~ doCreate('postgres', 'schema1.xml')

#~ doCreate('firebird', 'schema1.xml')

#~ doDiff('postgres', 'schema1.xml', 'schema2.xml')

#~ doDiff('postgres7', 'schema1.xml', 'schema2.xml')

os = OutputSamples()
os.createDoc()