xml2ddl
=======

Fork of the xml2ddl originally made by Berlios (http://xml2ddl.berlios.de).

XML to DDL
==========

This is a set of programs to create a database schema (structure) from an XML representation of the database.

There are 4 tools available:

xml2ddl outputs the SQL (aka DDL) statements to standard output.
 
    xml2ddl --dbms <dbms> <schema.xml>

diffxml2ddl does the same but only the changes required to bring <old-schema.xml> up-to-date with <new-schema.xml>

    diffxml2ddl --dbms <dbms> <new-schema.xml> [<old-schema.xml>]
 
xml2html creates one (currently) HTML file representation of the schema.

    xml2html [-f <outfile.html>] <schema.xml>
  
downloadXml.py Queries the server database and outputs it's resulting XML schema. Requires psycopg, MySQLdb or kinterbasdb.

    downloadXml --dbms <dbms> --database <database> --user <user> --pass <password>

\<dbms\> can (currently) be one of: postgres, postgres7, mysql, oracle, or firebird

More info available at index.html in the subdirectory doc.

Install
-------

    python setup.py install

or

    easy_install.py xml2ddl

Prerequesites
-------------

Requires Python 2.3 or greater

Tested with:

*    PostgreSQL version 7.3.4
*    PostgreSQL version 8.0.3
*    MySQL version 5.0.1-alpha-nt
*    Firebird version 1.5.1

License
-------

GNU GPL http://www.gnu.org/copyleft/gpl.html


You can find me on [Twitter](https://twitter.com/charlesnagy "Charlesnagy Twitter"), [My Blog](http://charlesnagy.info/ "Charlesnagy.info") or [LinkedIn](http://www.linkedin.com/in/nkaroly "Károly Nagy - MySQL DBA")
