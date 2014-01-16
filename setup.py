#!/usr/bin/env python

#from distutils.core import setup
from setuptools import setup
import glob
# Note to self:
# python setup.py sdist --formats=zip
# To create the zip file

# python setup.py --command-packages=setuptools.command bdist_egg
# To create the egg file

# python setup.py register
# to register with PyPI
# 

# Set this on command line
# DISTUTILS_DEBUG=true
# 
setup(
    name='xml2ddl',
    version='0.3.1',
    description="Xml to DDL is a set tools to convert an XML representation of a database into a set of SQL (or DDL) commands and vice versa.",
    long_description=
"""XML to DDL is a set of Python programs that converts an XML representation of a database into a set of SQL (or DDL commands - Data Definition Language) commands.
Also, you can download the XML metadata directly from your existing database.
Other tools exist to examine the difference between two XML schemas and output a sequence of SQL statements 
to change from one to the other (normally via ALTER statements).
There is also a tool to create HTML documentation from the XML. 
XML to DDL supports PostgreSQL, MySQL, Oracle and Firebird databases.
""",
    author='Scott Kirkwood',
    author_email='scott_kirkwood@users.berlios.de',
    url='http://xml2ddl.berlios.de/',
    download_url='http://developer.berlios.de/project/showfiles.php?group_id=2209&release_id=3368',
    keywords=['XML', 'SQL', 'DDL', 'ALTER', 'Database', 'AgileDB', 'PostgreSQL', 'MySQL', 'Firebird', 'Oracle', 'SQL99'],
    license='GNU GPL',
    platforms=['POSIX', 'Windows'],
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Operating System :: OS Independent',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Programming Language :: SQL',
        'Topic :: Database',
        'Topic :: Documentation',
        'Topic :: Software Development :: Code Generators',
        'Topic :: Text Processing :: Markup :: XML',
        'Topic :: Utilities',
    ], 
    scripts=[
        'scripts/xml2ddl', 
        'scripts/xml2html', 
        'scripts/diffxml2ddl',
        'scripts/downloadXml',
    ],
    packages=['xml2ddl'],
    package_data={'doc': ['*.html','*.pdf'],},
)
