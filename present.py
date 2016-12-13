#!/usr/bin/env python3

"""
This will simulate sending email results.
"""

import logging
import socketserver

import config
import pprint
import smtplib
import argparse
import datetime
import urllib.parse
import urllib.request

from email.mime.text import MIMEText
from lib import decrypt_and_deserialize, decode_decrypt_and_deserialize

logging.getLogger("gnupg").setLevel(logging.INFO)
logger = logging.getLogger('present')


def send_results(recipient_address, results, query_id):
    """
    If a sender email address is configured, we will try to send email from
    localhost.
    """
    if (config.EMAIL_SENDER):
        msg = MIMEText(results, 'plain')
        msg['Subject'] = 'Results for query {}'.format(query_id)
        msg['From'] = config.EMAIL_SENDER
        msg['To'] = recipient_address

        s = smtplib.SMTP('localhost')
        refused = s.send_message(msg)
        s.quit()
        return refused


def unwrap_metadata(metadata):
    """
    When data is merged, the field names are joined with their source (registry
    name). We have to to the same for metadata.
    """
    unwrapped_metadata = {}
    for source in metadata:
        for typ in metadata[source]:
            for fieldname in metadata[source][typ]:
                if typ not in unwrapped_metadata:
                    unwrapped_metadata[typ] = {}
                key = source + ":" + fieldname
                unwrapped_metadata[typ][key] = metadata[source][typ][fieldname]

    return unwrapped_metadata


def insert_intervals(fieldname, summary, metadata):
    """
    When data is put into categories by creating intervals by a simple
    division, we need to multiply the category identifier to get the original
    back. The multiplier is defined in the metadata.
    """
    if 'intervals' in metadata and fieldname in metadata['intervals']:
        return {float(key) * metadata['intervals'][fieldname]: value
                for key, value in summary.items()}


def insert_replacements(fieldname, summary, metadata):
    """
    Some category identifiers gives no meaning and should be replaced by values
    defined in metadta.
    """
    if 'replacements' in metadata and fieldname in metadata['replacements']:
        return {metadata['replacements'][fieldname][key]: value
                for key, value in summary.items()}


class PresentationHandler(socketserver.StreamRequestHandler):
    def handle(self):
        self.data = self.rfile.readline().strip()
        data = decode_decrypt_and_deserialize(self.data)

        query_id = data['query_id']
        email = data['email']
        logging.info("got data for query %s", query_id)

        if not "data" in data:
            # rejected: has no data or metadata
            decrypted_data = "Rejected"
            status = "rejected"

        else:
            # unwrap metadata organized per source
            metadata = {k: decrypt_and_deserialize(m)
                        for k, m in data["metadata"].items()}
            unwrapped_metadata = unwrap_metadata(metadata)

            # decrypt data and replace category names/labels
            decrypted_data = {}
            for encrypted_fieldname, categorized_summary in data["data"].items():
                fieldname = decrypt_and_deserialize(encrypted_fieldname)
                # replace interval categories from metadata
                summary = insert_intervals(fieldname, categorized_summary,
                                           unwrapped_metadata)
                if not summary:
                    # replace strings in keys from metadata
                    summary = insert_replacements(fieldname, categorized_summary,
                                                  unwrapped_metadata)
                if not summary:
                    summary = categorized_summary
                decrypted_data[fieldname] = summary

            # TODO: Logging is not the final delivery
            logger.info("decrypted summary for %s: %s",
                        query_id, decrypted_data)
            status = "ok"

        pretty = pprint.pformat(decrypted_data, indent=4)
        refused_addresses = send_results(email, pretty, query_id)
        sent_datetime = datetime.datetime.now()
        if refused_addresses:
            logger.warning("Could not send email to %s: %s",
                           email, refused_addresses)
        if refused_addresses is None:
            logger.info("Email sent to %s", email)

        # Now inform web server
        statusupdate = {'sent_datetime': sent_datetime,
                        'status': status,
                        'id': query_id}
        data = urllib.parse.urlencode(statusupdate).encode("utf-8")
        req = urllib.request.Request(config.WEB_SERVER_QUERY_STATUS_URL)
        req.add_header("Content-Type",
                       "application/x-www-form-urlencoded;charset=utf-8")
        res = urllib.request.urlopen(req, data)
        logger.debug("Status for sending this document is set: %s",
                     res.read().decode('utf-8'))

        self.request.sendall(bytes("", "utf-8"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Result presentation server")
    parser.add_argument('--debug', nargs='?', const=True, default=False,
                        help="Debug logging")
    args = parser.parse_args()

    level = logging.INFO
    if args.debug:
        level = logging.DEBUG

    logging.basicConfig(
        level=level,
        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
    )
    server = socketserver.TCPServer((config.PRESENTATION_SERVER_HOST,
                                     config.PRESENTATION_SERVER_PORT),
                                    PresentationHandler)
    server.serve_forever()
