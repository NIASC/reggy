Reggy — Biobank inventory
=========================

Components
----------

``web.py`` will run a web server form where users can create queries.

``query.py`` will serve the registries new queries and make them sign and
verify the queries before they are processed.

``registry.py`` will fetch queries from query server and push fake data to
the merge server, when registry owners accept the queries. For simulation, you
can accept or decline queries on port 5005. This will be removed in the future.

``merge.py`` runs a simple merge server that will merge data coming from
different registries.

``summarize.py`` is as service to do simple filtering (aka counting) on the
results.

``present.py`` will decrypt metadata and make everything understandable.

Dependencies
------------

* python3
* virtualenv for local installation without interfering with the systems
* pip to install other dependencies
* mongodb to store queries in a database on the web server. None of the secure
  servers will have a database added, everything will run in memory.

Installation
------------

    apt-get install python3-pip python3-virtualenv
    apt-get install build-essential python3-dev mongodb libssl-dev
    # the next will create a virtual python3 environment in the venv folder
    virtualenv --python /usr/bin/python3 venv
    # use the virtual python environment instead of the global environment
    source venv/bin/activate
    # install dependencies into the venv folder
    pip install -r requirements


Setup
-----

You need to generate some data for the fake registries:

    python generate_data.py

Usage
-----

For testing on a single computer, you will start the services in a lot of
terminals withing virtual Python environments. In a lot of terminals, run
``source venv/bin/activate`` and one of the services: web, query, merge,
summarize, registry. The lazy can paste this to run commands in tabs in a new
gnome-terminal window:

    gnome-terminal --tab -e "./venv/bin/python web.py" --tab -e "./venv/bin/python query.py" --tab -e "./venv/bin/python merge.py" --tab -e "./venv/bin/python summarize.py" --tab -e "./venv/bin/python present.py"

Then query data in ``localhost:5000/search``. The queries will probably need
data from multiple registries.

Now, running ``./venv/bin/python registry.py hunt`` to let the “hunt” service
sign all related queries and ``./venv/bin/python registry.py cancer`` to do the
same for the other service. Running these commands again will list all related,
signed queries, and list them with an ID.

Run ``./venv/bin/python registry.py hunt --accept ID`` (where ID is the long
ID) to accept the query. Do the same for other registries needed for the same
query, by replacing “hunt” with the registry name.

When all related registries have accepted the query, you should see some output
in the ``merge``, ``summarize`` and ``present`` services.

Configuration
-------------

There is a sample configuration file ``config.py`` that contains the
default configuration values. Change it and it should work.

Example keys have been installed for demo purposes, so everything should work.

Development roadmap
-------------------

* Sending email to let other try it
* Add security documentation
* Unit testing
* System testing, docker compose?

License
-------

Will get a nice and open license later. Probably GPL3 or AGPL3.
