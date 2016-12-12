Introduction to Reggy - Anonymized statistics from biobanks and health registries
=====================

Researchers have to wait for a long time just to know _if_ there are usable
data. Checking if there are data is the same process as getting the data. If
we can have anonymized summary statistics from health registries, we would
know if there are usable data almost instantly.

---------------------

Servers are set up with data owners, at their locations, with their preferred
security level. The datasets are selected by the data owners in collaboration
with the Reggy administrators and indexed for later searching.  All
communications are encrypted ([using public key cryptography
(Wikipedia)](https://en.wikipedia.org/wiki/Public-key_cryptography) and all
traffic will be initiated from the data owners’ side, not needing open ports on
these servers.

![Reggy overview](https://docs.google.com/drawings/d/slUK9N5GnkH7AD56HBtHSPA/image?w=603&h=346&rev=87&ac=1)

The data owner servers ask the Query server for new queries. First, the queries
are signed by all participants and sent back. The next step is to download the
signed queries, and check them before processing.

Then, data owners look up data, and send what is relevant according to the
query and their rules. The data sent is encrypted for the three different
recipients that will do work on parts of the result.

Example
-------

**Data owner 1**

| PID           | Age           | Genotyped  |
| ------------- | ------------- | ---------- |
| 1001002       | 46            | yes        |
| 1001003       | 64            | no         |
| 1001004       | 55            | yes        |
| 1001007       | 48            | yes        |
| 1001008       | 71            | no         |

**Data owner 2**

| PID           | Myocardial infarction | Stroke |
| ------------- | --------------------- | ------ |
| 1001002       | yes                   | no     |
| 1001003       | no                    | no     |
| 1001004       | no                    | no     |
| 1001005       | yes                   | no     |
| 1001007       | yes                   | yes    |

We see data from two data owners, having PIDs as personal identifiers. We are
interested in people that are genotyped from the data owner 1, and everybody
from data owner 2.

… To be continued … original in google document.
