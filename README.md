Reggy
=====

Biobank inventory
-----------------

CSV files contain dummy data

``merge.py`` runs a simple merge server on http://localhost:5000, that will merge data coming from different registries.

``summarize.py`` is as service to do simple filtering on the results.

``query.py`` will serve the registries new queries on http://localhost:5001.

``web.py`` will serve users a form where they can create queries

``reg.py [cancer|hunt]`` will fetch queries from _query_ servers and push fake data to the _merge_ server. Run for both fake registrys to get data to be merged. Merged results now show up in merge.py output. Will later be pushed to a result/filter/report/summary layer or two.

Dependencies
------------

* flask micro web server
* virtualenv to install flask as user
* pip to install the other two

    apt-get install python-pip python-virtualenv
    apt-get install build-essential python-dev mongodb  # for python-dev and mongodb
    # the next will specify where the virtual env is going to be located
    virtualenv venv
    # use the virtual python environment instead of the global environment
    source venv/bin/activate
    # install flask and the mongodb bindings in the venv folder
    pip install flask mongodb

Usage
-----

In a lot of terminals, run ``source venv/bin/activate`` and one of the services: web, query, merge, result. Then do a few queries from ``localhost:5000/search`` and run ``reg.py hunt`` and ``reg.py cancer``. There should hopefully be some status output in the terminal running the summarize command.

License
-------

Will get a nice and open license later. Probably GPL3 or AGPL3.
