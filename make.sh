cd tests
./dotests.sh
cd ../doc
./make_doc.sh
cd ..
python setup.py --command-packages=setuptools.command bdist_egg
python setup.py sdist --formats=zip
