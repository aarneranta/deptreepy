#!/usr/bin/env python3

# This file is adapted from the official UDPipe 2 client, available at
# <http://github.com/ufal/udpipe>.
#
# Copyright 2022 Institute of Formal and Applied Linguistics, Faculty of
# Mathematics and Physics, Charles University in Prague, Czech Republic.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import email.mime.multipart
import email.mime.nonmultipart
import email.policy
import json
import sys
import urllib.error
import urllib.request

__version__ = "2.1.1-dev"


def perform_request(server, method, params={}):
    if not params:
        request_headers, request_data = {}, None
    else:
        message = email.mime.multipart.MIMEMultipart("form-data", policy=email.policy.HTTP)

        for name, value in params.items():
            payload = email.mime.nonmultipart.MIMENonMultipart("text", "plain")
            payload.add_header("Content-Disposition", "form-data; name=\"{}\"".format(name))
            payload.add_header("Content-Transfer-Encoding", "8bit")
            payload.set_payload(value, charset="utf-8")
            message.attach(payload)

        request_data = message.as_bytes().split(b"\r\n\r\n", maxsplit=1)[1]
        request_headers = {"Content-Type": message["Content-Type"]}

    try:
        with urllib.request.urlopen(urllib.request.Request(
            url="{}/{}".format(server, method), headers=request_headers, data=request_data
        )) as request:
            return json.loads(request.read())
    except urllib.error.HTTPError as e:
        print("An exception was raised during UDPipe 'process' REST request.\n"
              "The service returned the following error:\n"
              "  {}".format(e.fp.read().decode("utf-8")), file=sys.stderr)
        raise
    except json.JSONDecodeError as e:
        print("Cannot parse the JSON response of UDPipe 'process' REST request.\n"
              "  {}".format(e.msg), file=sys.stderr)
        raise

def process(args):
    response = perform_request(args["service"], "process", args)
    if "model" not in response or "result" not in response:
        raise ValueError("Cannot parse the UDPipe 'process' REST request response.")

    #print("UDPipe generated an output using the model '{}'.".format(response["model"]), file=sys.stderr)
    #print("Please respect the model licence (CC BY-NC-SA unless stated otherwise).", file=sys.stderr)

    return response["result"]
