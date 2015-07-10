Reggy
=====

Biobank inventory
-----------------

CSV files contain dummy data

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

A presentation layer that will decrypt metadata and make data presentable will
be added in the future.

Dependencies
------------

* python3
* virtualenv for local installation without interfering with the systems
* pip to install other dependencies
* mongodb to store queries in a database on the web server. None of the secure
  servers will have a database added, everything will run in memory.

Instructions:

    apt-get install python3-pip python3-virtualenv
    apt-get install build-essential python3-dev mongodb libssl-dev
    # the next will create a virtual python3 environment in the venv folder
    virtualenv --python /usr/bin/python3 venv
    # use the virtual python environment instead of the global environment
    source venv/bin/activate
    # install dependencies into the venv folder
    pip install -r requirements

Usage
-----

In a lot of terminals, run ``source venv/bin/activate`` and one of the
services: web, query, merge, summarize, registry. The lazy can paste this to
run commands in tabs in a new gnome-terminal window:

    gnome-terminal --tab -e "./venv/bin/python web.py" --tab -e "./venv/bin/python query.py" --tab -e "./venv/bin/python registry.py" --tab -e "./venv/bin/python merge.py" --tab -e "./venv/bin/python summarize.py"

Then do a few queries from ``localhost:5000/search`` and do manual filtering
for the registries at ``localhost:5005``. There should hopefully be some status
output in the terminal running the summarize command.

Configuration
-------------

There is a sample configuration file ``config.example.json`` that contains the
default configuration values. This could (and should, in production) be copied
to ``config.json`` and changed.

License
-------

Will get a nice and open license later. Probably GPL3 or AGPL3.
