==========
XML To DDL
==========

.. meta::
   :keywords: XML, DDL, databases, generation
   :description lang=en: Creating DDL statements from XML


''Bringing some sanity to database maintenance.''

.. contents:: Table of Contents

Introduction
============

|xml2ddl| is a set of python programs to convert an XML representation of a database into a 
set of DDL_ (Data Definition Language) statements.

In addition |xml2ddl| can examine the difference between two XML files and output a sequence of ALTER statements that
will update the database to conform to the new schema.

Finallly, |xml2ddl| can generate HTML documentation of your schema.

You can find more information and download files at the `Berlios page <http://developer.berlios.de/projects/xml2ddl/>`_


Simple Example
==============

The following is a simple schema XML definition of a database::

    <schema>
        <table name="students" fullname="List of Students" 
            desc="List of students with their full names">
            <columns>
                <column name="id" fullname="Primary Key" inherits="index" key="1"
                    desc="Primary key for the table"/>
                <column name="student_name" fullname="Student Name" class="name" 
                    desc="The full name of the student Can this span multiple lines?"/>
            </columns>
        </table>
    </schema>
    
Here we run the program indicating output for PostgreSQL_::

    python xml2ddl.py --dbms postgres schema1.xml
    
We get the following output::

    DROP TABLE students;
    CREATE TABLE students (
		id integer,
		student_name varchar(80),
		CONSTRAINT pk_students PRIMARY KEY (id));
    COMMENT ON TABLE students IS 'List of students with their full names';
    COMMENT ON COLUMN students.id IS 'Primary key for the table';
    COMMENT ON COLUMN students.student_name IS 'The full name of the student';
    
If we run the program again for Firebird_::
    
	python xml2ddl.py --dbms firebird schema1.xml

we'll get different output::

	DROP TABLE students;
	CREATE TABLE students (
		id integer,
		student_name varchar(80),
	CONSTRAINT pk_students PRIMARY KEY (id));
	UPDATE RDB$RELATIONS SET RDB$DESCRIPTION = 'List of students with their full names'
		WHERE RDB$RELATION_NAME = upper('students');
	UPDATE RDB$RELATION_FIELDS SET RDB$DESCRIPTION = 'Primary key for the table'
		WHERE RDB$RELATION_NAME = upper('students') AND RDB$FIELD_NAME = upper('id');
	UPDATE RDB$RELATION_FIELDS SET RDB$DESCRIPTION = 'The full name of the student'
		WHERE RDB$RELATION_NAME = upper('students') AND RDB$FIELD_NAME = upper('student_name');
    
The example shows a feature of |xml2ddl|, database independence. 
Currently the program supports the Firebird_, PostgreSQL_, and MySQL_ databases, but more will probably become available.

Differencing Example
====================

Another key feature is the ability to examine the changes done to the XML and generate the DDL statements necessary 
to perform the changes to the database. If this is a new XML schema::

	<schema>
		<table name="students" fullname="List of Students" 
			desc="List of students with their full names">
			<columns>
				<column name="id" fullname="Primary Key" type="integer" key="1"
					desc="Primary key for the table"/>
				<column name="student_name" fullname="Student Name" type="varchar" size="80"
					desc="The full name of the student"/>
			</columns>
		</table>
	</schema>

Running this program::

	diffxml2ddl.py --dbms postgres schema2.xml schema1.xml

Produces the following DDL output::

	ALTER TABLE students ALTER student_name TYPE varchar(100);
	ALTER TABLE students ADD email varchar(100);
	COMMENT ON TABLE students IS 'List of students';

However, an older version of PostgreSQL doesn't support altering the column type::

	python diffxml2ddl.py --dbms postgres7 schema2.xml schema1.xml

The a temporary column needs to be created, the data copied over and the old column dropped::

	ALTER TABLE students ADD tmp_student_name varchar(80);
	UPDATE students SET tmp_student_name = student_name;
	ALTER TABLE students DROP student_name;
	ALTER TABLE students RENAME tmp_student_name TO student_name;
	ALTER TABLE students DROP email;
	COMMENT ON TABLE students IS 'List of students with their full names';

Using a dictionary
==================

If you find yourself repeating the same attributes in your XML schema over and over you can put these
in a dictionary::

    <dictionary name="column">
        <dict class="key" name="id" fullname="Primary Key" type="integer" null="no" key="1"
            desc="Primary key for the table" />
    </dictionary>

In this example we are telling the parser that the dictionary is for the nodes called ``column`` and when it sees the 
class ``key``, it should put in the the other attributes listed.  
So using this dictionary this would be equivalent:::

    ...
    <columns>
        <column class="key"/>
    </columns>
    ...

as::

    ...
    <columns>
        <column name="id" fullname="Primary Key" type="integer" null="no" key="1"
            desc="Primary key for the table"/>
    </columns>
    ...

In addition you can override any attributes in the dictionary, for example this::

    ...
    <columns>
        <column class="key" name="student_id"/>
    </columns>
    ...

would then be equivalent to::

    ...
    <columns>
        <column name="student_id" fullname="Primary Key" type="integer" null="no" key="1"
            desc="Primary key for the table"/>
    </columns>
    ...

The dictionaries can also support multiple inheritance through the ``inherits`` attribute.
Here's a rather contrived example::

	<dictionary name="column">
		<dict class="index" type="integer" null="no"/>
		<dict class="pk   key="1"/>
		<dict class="key" inherits="index,pk" name="id" fullname="Primary Key"
			desc="Primary key for the table"/>
	</dictionary>

Outputting HTML Documentation
=============================

Some of the attributes in the XML are used solely for documentation purposes.
For example, ``fullname`` has no equivalent in most DBMSs. 
Another, it ``deprecated`` which indicates that a column or table should no longer be used, but hasn't been deleted yet.

Here's how to output the HTML document::

    python xml2html.py --file schema.html schema.xml
    
Advantages
==========

Storing the schema in this form has some advantages:

1.  All the information about a table is stored together in one place. 
    Finding linked tables, sequence tables etc. should be simplified.

2.  Being text it can easily be stored in a VCS Repository, like Subversion_ or CVS_.

3.  Also because it is text you can compare differences between older and newer versions.
    In fact this is one of the main goals of this project.

4.  Since the description of the schema is abstract, it isn't tied to a specific database.

5.  Documentation can easily be generated from the XML schema.

6.  A pretty schema diagram can be drawn from the XML 
    `see Dia <http://www.lysator.liu.se/~alla/dia/>`_ and `Dot <http://www.graphviz.org/>`_ 
    (note, this functionality hasn't been implemented yet).

7.  A history of changes made to the table (by whom, when and why) can all be contained in the repository.
    Normally, metadata changes made to a database never stored anywhere.

8.  Migration scripts can be stored in the meta-data for certain changes that require the data to be modified.
    For example, if a column is split into two columns the procedure to make this modification can be
    stored into the repository (not implemented yet).
   
9.  Destructive changes can have backed ups made as part of its process. 
    For example, if a column is to be deleted that column along with its primary key(s) can be stored into a file.
    This way if they do undo the changes they can do so without needing to go to a full backup. (to do)

10. Additional useful information can be stored in the XML.
    Columns can be flagged as deprecated or obsolete, for example.

11. Scripts can be generated to automatically check that the data fits the domain.  
    For example, that status is 1, 2, 3, or 4 or that telephone numbers are in the format (999) 9999-99999. (to do)

12. Code can use the XML to it's own purposes.
    One example is to write code that figures out the best joins to use between two tables.
    Another example is to change a status code (ex. 1, 2, or 3) into an enumeration (ex. READY, PROCESSING, DONE).

To do
=====

Here are the major directions I see |xml2ddl| going:

* Support for more databases (currently I've written code only for PostgreSQL, Firebird, and MySQL).
* Build the XML schema from an existing database.
* Support comparing differences from the database as well as another XML file.
* More test cases.
* Support for database specific features

.. _PostgreSQL: http://www.postgresql.com/
.. _Firebird: http://firebird.sourceforge.net/
.. _MySQL: http://www.mysql.com/
.. _DDL: http://http://en.wikipedia.org/wiki/Data_Definition_Language
.. _Subversion: http://subversion.tigris.org/
.. _CVS: https://www.cvshome.org/

.. |xml2ddl| replace:: ``XML to DDL``
