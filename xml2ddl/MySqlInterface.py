#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
from downloadCommon import DownloadCommon, getSeqName
from DdlCommonInterface import DdlCommonInterface
import re

class MySqlDownloader(DownloadCommon):
    def __init__(self):
        self.strDbms = 'mysql'
        self.conn = None
    
    def connect(self, dbname, user, passwd, host, **kwargs):
        try:
            import MySQLdb
            # Get rid of the MySQLdb warnings
            import warnings
            warnings.simplefilter("ignore", MySQLdb.Warning)

        except:
            print "Missing MySQL support through MySQLdb"
            return
        self.conn = MySQLdb.connect(db=dbname, user=user, passwd=passwd, host=host, **kwargs)
        self.cursor = self.conn.cursor()


    @property
    def version(self):
        if not self.conn:
            return False
        if not hasattr(self, '_version'):
            self.cursor.execute('select @@version')
            _version = re.match('^([345])\.([0-9]+).*', self.cursor.fetchone()[0])
            if _version:
                self._version = _version.group(1), _version.group(2)
            
        return self._version 

    def useConnection(self, conn, version):
        self.conn = conn
        self.version = version
        self.cursor = self.conn.cursor()
        
    def getTables(self, tableList):
        """ Returns the list of tables as a array of strings """
        
        strQuery = "SHOW FULL TABLES"
        self.cursor.execute(strQuery)
        rows = self.cursor.fetchall()
        ret = []
        for row in rows:
            if len(row) == 1 or row[1] == 'BASE TABLE':
                ret.append(row[0])
        
        return self._confirmReturns(ret, tableList)
    
    def getTableColumns(self, strTable):
        """ Returns column in this format
            (strColumnName, strColType, nColSize, nColPrecision, bNotNull, strDefault, auto_increment)
        """
        re_size_prec = re.compile(r'(\w+)\((\d+),\s*(\d+)\)')
        re_size = re.compile(r'(\w+)\((\d+)\) (unsigned|signed)?')
        
        strQuery = "SHOW COLUMNS FROM `%s`" % (strTable)
        self.cursor.execute(strQuery)
        fullcols = self.cursor.fetchall()
        ret = []
        
        bAutoIncrement = False 
        for col in fullcols:
            (name, type, bNotNull, key, strDefault, extra) = col
            nColSize = None
            nColPrecision = None
            if extra == 'auto_increment':
                bAutoIncrement = True
            else:
                bAutoIncrement = False
            
            match = re_size_prec.match(type)
            if match:
                newType = match.group(1)
                nColSize = int(match.group(2))
                nColPrecision = int(match.group(3))
            else:
                match = re_size.match(type)
                if match:
                    newType = match.group(1) if not match.group(3) else '%s %s'%(match.group(1), match.group(3))
                    nColSize = int(match.group(2))
                    nColPrecision = None
                else:
                    newType = type
            
            if newType == "int":
                newType = 'integer'
                nColSize = None
                nColPrecision = None
                
            bNotNull = not (bNotNull == "YES")
            ret.append( (name, newType, nColSize, nColPrecision, bNotNull, strDefault, bAutoIncrement) )
        return ret
    
    def getTableComment(self, strTableName):
        """ Returns the comment as a string -- humm, no way to get the table comment? """
        
        return None

    def getTableOptions(self, strTableName):
        """ Returns a dictionary of table options """
        _map = [
            ('Engine', 1),
            ('Auto_increment', 10),
        ]
        _opts = dict()
        strQuery = "SHOW TABLE STATUS LIKE '%s'" % strTableName
        self.cursor.execute(strQuery)
        fullstat = self.cursor.fetchone()
        for attr, field in _map:
            _opts.update({attr: fullstat[field]})
        if fullstat[14]:
            _opts.update({'Default charset': self.getCharsetFromCollation(fullstat[14])})
        # Create options
        if fullstat[16]:
            for _cr_opts in fullstat[16].split(' '):
                _m = re.match('^([a-zA-Z_0-9]+)=([^ ]+)$', _cr_opts.strip())
                if _m:
                    _opts.update({_m.group(1): _m.group(2)})

        return dict([(k.upper(), v) for k, v in _opts.iteritems()])

    def getCharsetFromCollation(self, collation):
        self.cursor.execute("SHOW COLLATION LIKE %s", (collation, ))
        try:
            return self.cursor.fetchone()[1]
        except IndexError:
            # Failed to fetch it from the database
            # Trying fallback method
            _match = re.match('^(?P<charset>[a-zA-Z0-9]+)(_.*)?$', collation)
            if _match:
                return _match.group('charset')
            else:
                # This is probably should be tuned to return the default charset of the database or something
                return 'utf8'

    def getColumnComment(self, strTableName, strColumnName):
        """ Returns the comment as a string """
        strQuery = "SHOW FULL COLUMNS FROM `%s`" % (strTableName)
        self.cursor.execute(strQuery)
        fullcols = self.cursor.fetchall()
        strColumnName = strColumnName.lower()
        for col in fullcols:
            if len(col) == 7:
                (Field, Type, Null, Key, Default, Extra, Privileges) = col
                (Collation, Comment) = None, None
            else:
               (Field, Type, Collation, Null, Key, Default, Extra, Privileges, Comment) = col
            
            if Field.lower() == strColumnName:
                return Comment
        
        return None

    def getTableIndexes(self, strTableName):
        """ Returns 
            (strIndexName, [strColumns,], bIsUnique, bIsPrimary, bIsClustered)
            or []
        """
        strQuery = 'show index from `%s`' % (strTableName)
        self.cursor.execute(strQuery)
        indexes = self.cursor.fetchall()

        ret = []
        keyMap = {}
        for index in indexes:
            (Table, Non_unique, Key_name, Seq_in_index, Column_name, Collation, Cardinality, Sub_part, Packed, Null, Index_type, Comment) = index[:12]
            if Key_name == 'PRIMARY':
                bIsPrimary = True
            else:
                bIsPrimary = False
            
            if Non_unique == 0:
                bIsUnique = False
            else:
                bIsUnique = True
            
            if Key_name in keyMap:
                #FIX: TODO: make sure the keys are in order.
                keyMap[Key_name][1].append(Column_name)
            else:
                keyMap[Key_name] = (Key_name, [Column_name], bIsUnique, bIsPrimary, Packed)
                ret.append( keyMap[Key_name] )
        
        return ret

    def getTableRelations(self, strTableName):
        """ Returns 
            (strConstraintName, colName, fk_table, fk_columns, confupdtype, confdeltype))
            or []
        """
        re_ref = re.compile(r'\s*CONSTRAINT\s+`(\w+)`\s+FOREIGN KEY\s+\(([^)]+)\)\s+REFERENCES\s+`(\w+)`\s+\(([^)]+)\)( ON DELETE (?:[A-Z]+))?( ON UPDATE (?:[A-Z]+))?')
        """ex. CONSTRAINT `fk_category_id` FOREIGN KEY (`category_id`) REFERENCES `categories` (`id`),"""
        
        # TODO
        delType = ''
        updateType = ''
        
        strQuery = 'SHOW CREATE TABLE `%s`' % (strTableName)
        self.cursor.execute(strQuery)
        rows = self.cursor.fetchall()
        ret = []
        for line in rows[0][1].split('\n'):
            match = re_ref.match(line)
            if match:
                myCols = [ str.strip()[1:-1] for str in match.group(2).split(',') ]
                fkCols = [ str.strip()[1:-1] for str in match.group(4).split(',') ]
                delType = self.mapMySqlOnSomething(match.group(5))
                updateType = self.mapMySqlOnSomething(match.group(6))
                ret.append( ( match.group(1), myCols, match.group(3), fkCols, delType, updateType) )
        
        return ret
        
    def mapMySqlOnSomething(self, strStr):
        if strStr == None:
            return None
        
        if strStr.endswith('CASCADE'):
            return 'c'
        
        if strStr.endswith('RESTRICT'):
            return 'r'
        
        if strStr.endswith('NULL'):
            return 'n'
            
        if strStr.endswith('DEFAULT'):
            return 'd'
        
        return 'a'
        
    def getViews(self, viewList):
        if self.version[0] < 5:
            return []
        
        strQuery = "SHOW FULL TABLES"
        self.cursor.execute(strQuery)
        rows = self.cursor.fetchall()
        ret = []
        for row in rows:
            if len(row) > 1 and row[1] == 'VIEW':
                ret.append(row[0])
                
        return self._confirmReturns(ret, viewList)
        
    def getViewDefinition(self, strViewName):
        strQuery = "SHOW CREATE VIEW `%s`" % (strViewName)
        try:
            self.cursor.execute(strQuery)
        except:
            return ''
        rows = self.cursor.fetchall()
        if rows:
            ret = rows[0][1]
            # ext CREATE VIEW test.v AS select 1 AS `a`,2 AS `b`
            # CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY INVOKER VIEW `SiteExperimentFullOnSummary` AS select
            reGetDef = re.compile('CREATE (?:ALGORITHM=[^ ]+ )?(?:DEFINER=`[^`]+`@`[^`]+` )?(?:SQL SECURITY INVOKER )?VIEW [a-zA-Z0-9_$`\.]+ AS (.*)')
            match = reGetDef.match(ret)
            if match:
                return match.group(1)
            else:
                print "Didn't match %s" % (ret)
            
            return ret
        
        return ''
        
    def getFunctions(self, functionList):
        """ Returns functions """
        
        # TODO handle the functionList
        return []
        strQuery = "SHOW FUNCTION STATUS"
        try:
            self.cursor.execute(strQuery)
        except:
            return []
        rows = self.cursor.fetchall()
        if rows:
            return self._confirmReturns([x[1] for x in rows], funcionList)
        
        return []

    def getFunctionDefinition(self, strSpecifiName):
        """ Returns (routineName, parameters, return, language, definition) """
        
        strQuery = "SHOW CREATE FUNCTION `%s`" % (strSpecifiName)
        self.cursor.execute(strQuery)
        rows = self.cursor.fetchall()
        if not rows:
            return (None, None, None, None)
        
        
        strCreate = rows[0][2]
        # ex.CREATE FUNCTION `test`.`sales_tax`(subtotal real) RETURNS real BEGIN    RETURN subtotal * 0.06;END
        re_createFunc = re.compile(r'\s* CREATE \s+ FUNCTION \s+ ([\w`\.-]*) \s* \( ([^)]*) \) \s+ RETURNS \s+ (\w+) \s+ (.*)', re.DOTALL | re.MULTILINE | re.VERBOSE)
        match = re_createFunc.match(strCreate)
        if match:
            strParams = match.group(2).split(',')
            strReturns = match.group(3)
            strLanguage = ''
            strDefinition = match.group(4)
        else:
            print "'%s'" % (strCreate)
            strParams = []
            strReturns = ''
            strLanguage = ''
            strDefinition = strCreate
            
        return (strSpecifiName, strParams, strReturns, strLanguage, strDefinition)

class DdlMySql(DdlCommonInterface):
    def __init__(self):
        DdlCommonInterface.__init__(self, 'mysql')
        self.params['max_id_len'] = { 'default' : 64 }
        self.params['quote_l'] = '`'
        self.params['quote_r'] = '`'
        self.params['table_desc'] = ["ALTER TABLE %(table)s COMMENT %(desc)s"]
        self.params['change_col_type'] = ['ALTER TABLE %(table_name)s MODIFY %(column_name)s %(column_type)s']
        self.params['column_desc'] = ["ALTER TABLE %(table)s MODIFY %(column)s %(type)sCOMMENT %(desc)s"]
        self.params['has_auto_increment'] = True
        self.params['can_change_table_comment'] = False
        self.params['add_key_constraint'] = ['ALTER TABLE %(table_name)s ADD PRIMARY KEY (%(keys)s)']
        self.params['drop_index'] = ['DROP INDEX %(index_name)s ON %(table_name)s']
        self.params['drop_default'] = ['ALTER TABLE %(table_name)s MODIFY %(column_name)s %(column_type)s']
        self.params['rename_column'] = ['ALTER TABLE %(table_name)s CHANGE %(old_col_name)s %(new_col_name)s %(column_type)s']
        self.params['keywords'] = """
            ADD ALL ALTER ANALYZE AND AS ASC ASENSITIVE AUTO_INCREMENT BDB BEFORE BERKELEYDB BETWEEN BIGINT BINARY
            BLOB BOTH BY CALL CASCADE CASE CHANGE CHAR CHARACTER CHECK COLLATE COLUMN COLUMNS CONDITION CONNECTION
            CONSTRAINT CONTINUE CREATE CROSS CURRENT_DATE CURRENT_TIME CURRENT_TIMESTAMP CURSOR DATABASE 
            DATABASES DAY_HOUR DAY_MICROSECOND DAY_MINUTE DAY_SECOND DEC DECIMAL DECLARE DEFAULT DELAYED DELETE DESC
            DESCRIBE DETERMINISTIC DISTINCT DISTINCTROW DIV DOUBLE DROP ELSE ELSEIF ENCLOSED ESCAPED EXISTS EXIT 
            EXPLAIN FALSE FETCH FIELDS FLOAT FOR FORCE FOREIGN FOUND FRAC_SECOND FROM FULLTEXT GRANT GROUP
            HAVING HIGH_PRIORITY HOUR_MICROSECOND HOUR_MINUTE HOUR_SECOND IF IGNORE IN INDEX INFILE INNER INNODB
            INOUT INSENSITIVE INSERT INT INTEGER INTERVAL INTO IO_THREAD IS ITERATE JOIN KEY KEYS KILL LEADING
            LEAVE LEFT LIKE LIMIT LINES LOAD LOCALTIME LOCALTIMESTAMP LOCK LONG LONGBLOB LONGTEXT LOOP LOW_PRIORITY 
            MASTER_SERVER_ID MATCH MEDIUMBLOB MEDIUMINT MEDIUMTEXT MIDDLEINT MINUTE_MICROSECOND MINUTE_SECOND MOD NATURAL
            NOT NO_WRITE_TO_BINLOG NULL NUMERIC ON OPTIMIZE OPTION OPTIONALLY OR ORDER OUT OUTER OUTFILE PRECISION PRIMARY
            PRIVILEGES PROCEDURE PURGE READ REAL REFERENCES REGEXP RENAME REPEAT REPLACE REQUIRE RESTRICT RETURN REVOKE RIGHT
            RLIKE SECOND_MICROSECOND SELECT SENSITIVE SEPARATOR SET SHOW SMALLINT SOME SONAME SPATIAL SPECIFIC
            SQL SQLEXCEPTION SQLSTATE SQLWARNING SQL_BIG_RESULT SQL_CALC_FOUND_ROWS SQL_SMALL_RESULT SQL_TSI_DAY 
            SQL_TSI_FRAC_SECOND SQL_TSI_HOUR SQL_TSI_MINUTE SQL_TSI_MONTH SQL_TSI_QUARTER SQL_TSI_SECOND SQL_TSI_WEEK
            SQL_TSI_YEAR SSL STARTING STRAIGHT_JOIN STRIPED TABLE TABLES TERMINATED THEN TIMESTAMPADD TIMESTAMPDIFF TINYBLOB
            TINYINT TINYTEXT TO TRAILING TRUE UNDO UNION UNIQUE UNLOCK UNSIGNED UPDATE USAGE USE USER_RESOURCES USING
            UTC_DATE UTC_TIME UTC_TIMESTAMP VALUES VARBINARY VARCHAR VARCHARACTER VARYING WHEN WHERE WHILE WITH
            WRITE XOR YEAR_MONTH ZEROFILL""".split() 

    # Tables
    def addTable(self, strTableName, colDefs, keys, strTableStuff, diffs):
        info = {
            'table_name' : self.quoteName(strTableName),
            'col_defs'   : ',\n  '.join(colDefs),
            'primary_keys' : '\n',
            'extra'      : strTableStuff,
        }
        if len(keys) > 0:
            info['primary_keys'] = ',\n  PRIMARY KEY (%s)' % ','.join(keys)

        for strDdl in self.params['add_table']:
            diffs.append(('Create Table', strDdl % info))


    def quoteName(self, strName):
        if strName[0] == self.params['quote_l'] and strName[-1] == self.params['quote_r']:
            return strName
        return self.params['quote_l'] + strName + self.params['quote_r']
            
    def dropKeyConstraint(self, strTable, strConstraintName, diffs):
        """ Can't drop constraints """
        pass

    def dropRelation(self, strTableName, strRelationName, diffs):
        """ Can't drop relations """
        pass


    def addFunction(self, strNewFunctionName, argumentList, strReturn, strContents, attribs, diffs):
        argumentList = [ '%s' % arg for arg in argumentList ]
        info = {
            'functionname' : self.quoteName(strNewFunctionName),
            'arguments'  : ', '.join(argumentList),
            'returns'  : strReturn,
            'contents' : strContents.replace("'", "''"),
            'language' : '',
        }
        if 'language' in attribs:
            info['language'] = ' LANGUAGE %s' % (attribs['language'])

        diffs.append(('Add function',  # OR REPLACE 
            "CREATE FUNCTION %(functionname)s(%(arguments)s) RETURNS %(returns)s %(language)s\n%(contents)s" % info )
        )

    def dropFunction(self, strOldFunctionName, argumentList, diffs):
        info = {
            'functionname' : self.quoteName(strOldFunctionName),
        }
        diffs.append(('Drop function',
            'DROP FUNCTION %(functionname)s' % info)
        )
