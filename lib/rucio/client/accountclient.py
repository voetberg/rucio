# Copyright European Organization for Nuclear Research (CERN)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# You may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
#
# Authors:
# - Thomas Beermann, <thomas.beermann@cern.ch>, 2012
# - Vincent Garonne, <vincent.garonne@cern.ch>, 2012


"""
Client classes for callers of the Rucio system
"""

import json
import requests

from rucio.client import Client
from rucio.common.utils import build_url


class AccountClient(Client):

    """Account client class for working with rucio accounts"""

    def __init__(self, host, port=None, account=None, use_ssl=False, auth_type=None, creds=None):
        super(AccountClient, self).__init__(host, port, account, use_ssl, auth_type, creds)

    def create_account(self, accountName):
        """
        Sends the request to create a new account.

        :param accountName: the name of the account.
        :return: True if account was created successfully else False.
        :raises Duplicate: if account already exists.
        """

        headers = {'Rucio-Auth-Token': self.auth_token, 'Rucio-Type': 'user'}
        path = 'account/' + accountName
        url = build_url(self.host, path=path, use_ssl=self.use_ssl)

        r = self._send_request(url, headers, type='PUT')

        if r.status_code == requests.codes.created:
            return True
        else:
            exc_cls, exc_msg = self._get_exception(r.text)
            raise exc_cls(exc_msg)

    def disable_account(self, accountName):
        """
        Sends the request to disable an account.

        :param accountName: the name of the account.
        :return: True is account was disabled successfully. False otherwise.
        :raises AccountNotFound: if account doesn't exist.
        """

        headers = {'Rucio-Auth-Token': self.auth_token}
        path = 'account/' + accountName
        url = build_url(self.host, path=path, use_ssl=self.use_ssl)

        r = self._send_request(url, headers, type='DEL')

        if r.status_code == requests.codes.ok:
            return True
        else:
            exc_cls, exc_msg = self._get_exception(r.text)
            raise exc_cls(exc_msg)

    def get_account(self, accountName):
        """
        Sends the request to get information about a given account.

        :param accountName: the name of the account.
        :return: a list of attributes for the account. None if failure.
        :raises AccountNotFound: if account doesn't exist.
        """

        headers = {'Rucio-Auth-Token': self.auth_token}
        path = 'account/' + accountName
        url = build_url(self.host, path=path, use_ssl=self.use_ssl)
        r = self._send_request(url, headers)

        if r.status_code == requests.codes.ok:
            acc = json.loads(r.text)
            return acc
        else:
            exc_cls, exc_msg = self._get_exception(r.text)
            raise exc_cls(exc_msg)

    def list_accounts(self):
        """
        Sends the request to list all rucio accounts.

        :return: a list containing the names of all rucio accounts.
        :raises AccountNotFound: if account doesn't exist.
        """

        headers = {'Rucio-Auth-Token': self.auth_token}
        path = 'account/'
        url = build_url(self.host, path=path, use_ssl=self.use_ssl)

        r = self._send_request(url, headers)
        if r.status_code == requests.codes.ok:
            accounts = json.loads(r.text)
            return accounts
        else:
            exc_cls, exc_msg = self._get_exception(r.text)
            raise exc_cls(exc_msg)
