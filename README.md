Reggy
=====

Biobank inventory
-----------------

CSV files contain dummy data

``merge.py`` runs a simple merge server on http://localhost:5000, that will
merge data coming from different registries.

``summarize.py`` is as service to do simple filtering (aka counting) on the
results.

``query.py`` will serve the registries new queries on http://localhost:5001.

``web.py`` will serve users a form where they can create queries

``registry.py`` will fetch queries from _query_ servers and push fake data to
the _merge_ server, when registry owners accept the queries.

Dependencies
------------

* flask micro web server
* mongodb to store queries in a database
* virtualenv to install flask as user
* pip to install the other two

Instructions:

    apt-get install python-pip python-virtualenv
    apt-get install build-essential python-dev mongodb  # for python-dev and mongodb
    # the next will specify where the virtual env is going to be located
    virtualenv2 venv
    # use the virtual python environment instead of the global environment
    source venv/bin/activate
    # install flask and the mongodb bindings in the venv folder
    pip install flask pymongo python-gnupg

Usage
-----

In a lot of terminals, run ``source venv/bin/activate`` and one of the
services: web, query, merge, summarize, registry. Then do a few queries from
``localhost:5000/search`` and do manual filtering for the registries at
``localhost:5005``. There should hopefully be some status output in the
terminal running the summarize command.

Configuration
-------------

There is a sample configuration file ``config.example.json`` that contains the
default configuration values. This could (and should, in production) be copied
to ``config.json`` and changed.

License
-------

Will get a nice and open license later. Probably GPL3 or AGPL3.
