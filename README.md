Reggy
=====

Biobank inventory
-----------------

CSV files contain dummy data

``merge.py`` runs a simple merge server on http://localhost:5000, that will merge data coming from different registrys.

``reg.py [cancer|hunt] query_id`` will push data from fake registrys to the merge server. Run for both fake registrys to get data to be merged. Merged results now show up in merge.py output.

Dependencies
------------

* flask micro web server
* virtualenv to install flask as user
* pip to install the other two

License
-------

Will get a nice and open license later. Probably GPL3 or AGPL3.
