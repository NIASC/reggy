Security considerations
=======================

No part of the system should get more information than it need.

- Security
- Privacy

To keep the system as secure as possible, it is spread as services across
different servers, owned by different entities. If malicious people get access
to one part, it should not be possible for them to trick the system into giving
them more information than needed.

The information about who makes queries is public. What kind of queries they
make is also public. This gives transparency about what the system is used for,
so that individuals and organizations can trust it. One could argue that the
results should be made public as well, for transparency reasons.

Communications between services is using [public key cryptography][pubkey], where the
sender is encrypting the information with the recipients public key, so that
only the recipient service is able to extract the information, using its
private key.

Query verification
------------------

A data owner server will ask for a list of queries to respond to. This triggers
a fetch a list of queries from the web server. Then each registry that is going
to see this query has to cryptographically sign it first, and when all
participating data owner servers have signed it, it is cryptographically
verified at each recipient, in a way that every participant verifies all other
participants’ signatures. We need this in case the query server had been
compromised and made into tricking participants into sending too much, but
giving out different queries to different participants.

Different recipients having different keys
------------------------------------------

When participants send data to the merge server, it is encrypted for the
different recipients. The ids used when merging are encrypted using the merge
server’s public key. The data so summarize is encrypted using the summary
servers’s public key, and the metadata to explain it all is encrypted with the
presentation server’s public key. All of this is sent to the merge server,
which is only able to decrypt the intended information.

Pseudonymizing or anonymizing data
----------------------------------

IDs used for merging is generated from project IDs using a secret that is
common to the participating data owner servers. This is created by using
[Scrypt][scrypt] to make it harder to reverse engineer. The secret used one
time only, and consists of a common secret from the query server in addition to
using the signed query itself as input.

Having a shared secret is considered a weak point in the system, but necessary
to be able to generate the same “hashed” IDs needed to merge the data. The data
itself is encrypted in a way that the merge server is not able to decrypt it,
but the summary server can.

The merge server will discard the IDs before passing data to the summary server.

Decrypting data and summarizing
-------------------------------

All data, except for the above mentioned IDs, passes through the merge server
encrypted. The data is encrypted at the summary server, before making a summary
of the data, thus making the data non-individual. The data itself is not passed
on to the presentation server, only the summary (and the encrypted metadata
sent between data owner and the presentation server).

If compromised, there is a lot of information passing through the summary
server, and it is possible to analyze this and gain some useful information.
But this information is de-identified (by having no IDs and our
[filtering](#filtering) should avoid sending too few or identifiable values)
and the values are categorized or standardized, and should be hard to get.

Making data presentable
-----------------------

Data output from the summary is not meant to be understandable. We have a
separate level to make data presentable before sending out reports. This level
is added to do as little as possible in the steps where security is more
important.

The presentation level will take categorized values and replace the category
identifiers by the real meaning, using metadata coming encrypted from the data
owner servers through the merge and summary servers. All keys describing the
data will also be come in encrypted form and be decrypted and inserted into the
final “reports” at this step.

The results could be regarded as public information, but we will just send them
by email. A notification to the web server is also sent to mark the query as
finished, containing the query ID and timestamp.

Server ownership
----------------

Data owners will have one server installed inside their firewall, where they
have full access and daily maintenance responsibility. Reggy updates will be
provided as software packages that they will install.

The other and servers, and thereby the control over the system, should be
spread out with different organizational entities. One could argue that the web
and presentation servers could be located at the same organization, or at the
same physical server.

Future work
-----------

- More documentation
- Good illustrations
- Do we need extra salt, or is using the decrypted signed query itself good
  input?
- Find a way to run hash the running code (except a minimum set of
  configuration) to make sure the code at participating servers are not
  tampered with.
- Set up automatic testing using Docker containers or virtual machines to make
  it easy for others to download and test.

[pubkey]: https://en.wikipedia.org/wiki/Public-key_cryptography
[scrypt]: https://en.wikipedia.org/wiki/Scrypt
