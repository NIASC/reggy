Reggy
=====

Biobank inventory
-----------------

CSV files contain dummy data

``merge.py`` runs a simple merge server on http://localhost:5000, that will merge data coming from different registrys.

``query.py`` will serve the registry new queries on http://localhost:5001.

``reg.py [cancer|hunt]`` will push data from fake registrys to the merge server. Run for both fake registrys to get data to be merged. Merged results now show up in merge.py output. Will later be pushed to a result/filter/report/summary layer or two.

Dependencies
------------

* flask micro web server
* virtualenv to install flask as user
* pip to install the other two

* apt-get install python-pip python-virtualenv
* virtualenv venv (to say where virtual env is going to be installed)
* source venv/bin/activate
* (you are now in a virtual python environment with less restrictions)
* pip install flask (will save flask under the venv folder)

License
-------

Will get a nice and open license later. Probably GPL3 or AGPL3.
