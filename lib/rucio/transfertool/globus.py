# Copyright European Organization for Nuclear Research (CERN) since 2012
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
import logging
import os

from rucio.common.config import config_get, config_get_int
from rucio.common.constants import RseAttr
from rucio.common.extra import import_extras
from rucio.common.utils import chunks
from rucio.db.sqla.constants import RequestState
from rucio.transfertool.transfertool import TransferStatusReport, Transfertool, TransferToolBuilder

EXTRA_MODULES = import_extras(['globus_sdk'])

if EXTRA_MODULES['globus_sdk']:
    # View the SDK docs - https://globus-sdk-python.readthedocs.io/en/stable/
    import globus_sdk


def bulk_group_transfers(transfer_paths, policy='single', group_bulk=200):
    """
    Group transfers in bulk based on certain criteria

    :param transfer_paths:  List of (potentially multihop) transfer paths to group. Each path is a list of single-hop transfers.
    :param policy:          Policy to use to group.
    :param group_bulk:      Bulk sizes.
    :return:                List of transfer groups
    """
    if policy == 'single':
        group_bulk = 1

    grouped_jobs = []
    for chunk in chunks(transfer_paths, group_bulk):
        # Globus doesn't support multihop. Get the first hop only.
        transfers = [transfer_path[0] for transfer_path in chunk]

        grouped_jobs.append({
            'transfers': transfers,
            # Job params are not used by globus transfertool, but are needed for further common fts/globus code
            'job_params': {}
        })

    return grouped_jobs


class GlobusTransferStatusReport(TransferStatusReport):

    supported_db_fields = [
        'state',
        'external_id',
    ]

    def __init__(self, request_id, external_id, globus_response):
        super().__init__(request_id)

        if globus_response == 'FAILED':
            new_state = RequestState.FAILED
        elif globus_response == 'SUCCEEDED':
            new_state = RequestState.DONE
        else:
            new_state = RequestState.SUBMITTED

        self.state = new_state
        self.external_id = None
        if new_state in [RequestState.FAILED, RequestState.DONE]:
            self.external_id = external_id

    def initialize(self, session, logger=logging.log):
        pass

    def get_monitor_msg_fields(self, session, logger=logging.log):
        return {'protocol': 'globus'}


class GlobusTransferTool(Transfertool):
    """
    Globus implementation of Transfertool abstract base class
    """

    external_name = 'globus'
    service_name = 'rucio-globus-transfers'
    required_rse_attrs = (RseAttr.GLOBUS_ENDPOINT_ID, )

    def __init__(self, external_host, logger=logging.log, group_bulk=200, group_policy='single'):
        """
        Initializes the transfertool

        :param external_host:   The external host where the transfertool API is running
        """
        if not external_host:
            external_host = 'Globus Online Transfertool'
        super().__init__(external_host, logger)
        self.group_bulk = group_bulk
        self.group_policy = group_policy
        self.CLIENT_AUTH_APP = config_get("conveyor", "globus_auth_app", raise_exception=True)
        self.sync_level = config_get("conveyor", "globus_sync_level", raise_exception=False, default='checksum')
        self.globus_task_deadline = config_get_int('conveyor', 'globus_task_deadline', False, 2880)

    def __read_secrets(self) -> tuple[str, str]:
        self.logger.debug("Loading auth scerets from %s" % self.CLIENT_AUTH_APP)
        if not os.path.exists(self.CLIENT_AUTH_APP):
            raise Exception("Could not find client auth file")  # TODO Specific exceptions

        try:
            with open(self.CLIENT_AUTH_APP, 'r') as f:
                lines = f.read().strip().split('\n')

                if len(lines) < 2:
                    raise ValueError("Auth file must contain at least 2 lines (client_id and client_secret)")

                client_id = lines[0].strip()
                client_secret = lines[1].strip()

                # Validate that we got non-empty values
                if not client_id:
                    raise ValueError("Empty client_id in auth file")
                if not client_secret:
                    raise ValueError("Empty client_secret in auth file")

        except OSError as error:
            raise Exception("I/O error({0}): {1}".format(error.errno, error.strerror))

        return client_id, client_secret

    def client_app(self) -> globus_sdk.ConfidentialAppAuthClient:
        # Refer to: https://globus-sdk-python.readthedocs.io/en/stable/examples/client_credentials.html#using-clientcredentialsauthorizer
        client_id, client_secret = self.__read_secrets()
        return globus_sdk.ConfidentialAppAuthClient(client_id=client_id, client_secret=client_secret)

    def transfer_client(self, client_app: globus_sdk.ConfidentialAppAuthClient) -> globus_sdk.TransferClient:
        # Authorize with the secrets
        cc_authorizer = globus_sdk.ClientCredentialsAuthorizer(client_app, globus_sdk.TransferClient.scopes.all)
        return globus_sdk.TransferClient(app=cc_authorizer)

    def build_transfer_data(self, data_paths: dict[str, str], job_label: str, source_endpoint_id: str, destination_endpoint_id: str) -> globus_sdk.TransferData:
        deadline = datetime.datetime.utcnow() + datetime.timedelta(minutes=self.globus_task_deadline)
        tdata = globus_sdk.TransferData(
            source_endpoint_id,
            destination_endpoint_id,
            label=job_label,
            sync_level=self.sync_level,
            deadline=deadline,
        )
        for source, dest in data_paths.items():
            tdata.add_item(source, dest)
        return tdata

    def build_delete_data(self, delete_items: list[str], endpoint_id: str, recursive: bool = False) -> globus_sdk.DeleteData:
        now = datetime.datetime.utcnow()
        deadline = now + datetime.timedelta(minutes=self.globus_task_deadline)
        ddata = globus_sdk.DeleteData(
            endpoint=endpoint_id,
            label=f"delete-{now.strftime('%Y%m%d%H%M%s')}",
            recursive=recursive,
            deadline=deadline
        )
        for item in delete_items:
            ddata.add_item(item)
        return ddata

    @classmethod
    def submission_builder_for_path(cls, transfer_path, logger=logging.log):
        hop = transfer_path[0]
        if not cls.can_perform_transfer(hop.src.rse, hop.dst.rse):
            logger(logging.WARNING, "Source or destination globus_endpoint_id not set. Skipping {}".format(hop))
            return [], None

        return [hop], TransferToolBuilder(cls, external_host='Globus Online Transfertool')

    def group_into_submit_jobs(self, transfer_paths):
        jobs = bulk_group_transfers(transfer_paths, policy=self.group_policy, group_bulk=self.group_bulk)
        return jobs

    def submit_one(self, files, timeout=None):
        """
        Submit transfers to globus API

        :param files:        List of dictionaries describing the file transfers.
        :param job_params:   Dictionary containing key/value pairs, for all transfers.
        :param timeout:      Timeout in seconds.
        :returns:            Globus transfer identifier.
        """

        source_path = files[0]['sources'][0]
        self.logger(logging.INFO, 'source_path: %s' % source_path)

        source_endpoint_id = files[0]['metadata']['source_globus_endpoint_id']

        # TODO: use prefix from rse_protocol to properly construct destination url
        # parse and assemble dest_path for Globus endpoint
        dest_path = files[0]['destinations'][0]
        self.logger(logging.INFO, 'dest_path: %s' % dest_path)

        # TODO: rucio.common.utils.construct_url logic adds unnecessary '/other' into file path
        # s = dest_path.split('/') # s.remove('other') # dest_path = '/'.join(s)

        destination_endpoint_id = files[0]['metadata']['dest_globus_endpoint_id']
        job_label = files[0]['metadata']['request_id']

        submit_data = self.build_transfer_data(
            {source_path: dest_path},
            job_label=job_label,
            source_endpoint_id=source_endpoint_id,
            destination_endpoint_id=destination_endpoint_id
        )
        transfer_result = self._create_transfer_request(submit_data)
        task_id = transfer_result['task_id']
        return task_id

    def _create_transfer_request(self, transfer_data: globus_sdk.TransferData) -> globus_sdk.GlobusHTTPResponse:
        with self.client_app() as client_app:
            with self.transfer_client(client_app) as transfer_client:
                transfer_result = transfer_client.submit_transfer(transfer_data)
        return transfer_result

    def submit(self, transfers, job_params, timeout=None):
        """
        Submit a bulk transfer to globus API

        :param transfers:    List of dictionaries describing the file transfers.
        :param job_params:   Not used by Globus Transfsertool
        :param timeout:      Timeout in seconds.
        :returns:            Globus transfer identifier.
        """
        self.logger(logging.DEBUG, '... Starting globus xfer ...')

        source_globus_id = [t.src.rse.attributes[RseAttr.GLOBUS_ENDPOINT_ID] for t in transfers]
        if len(set(source_globus_id)) != 1:
            raise Exception("More than one source RSE detected for transfer!")
        source_globus_id = source_globus_id[0]

        dest_globus_id = [t.dst.rse.attributes[RseAttr.GLOBUS_ENDPOINT_ID] for t in transfers]
        if len(set(dest_globus_id)) != 1:
            raise Exception("More than one destination RSE detected for transfer!")
        dest_globus_id = dest_globus_id[0]

        task_name = [t.rws.name for t in transfers][0]
        self.logger.debug("Using %s as transfer job label" % task_name)

        transfer_paths = {}
        for transfer in transfers:
            for src in transfer.sources:
                dst = transfer.dest_url
                transfer_paths[src] = dst

        tdata = self.build_transfer_data(
            transfer_paths,
            source_endpoint_id=source_globus_id,
            destination_endpoint_id=dest_globus_id,
            job_label=task_name
        )

        self.logger.debug(
            "submitting transfer with data - " + str(tdata)
        )

        task_id = self._create_transfer_request(transfer_data=tdata)['task_id']
        return task_id

    def bulk_query(self, requests_by_eid, timeout=None):
        """
        Query the status of a bulk of transfers in globus API

        :param requests_by_eid: dictionary {external_id1: {request_id1: request1, ...}, ...}
        :returns: Transfer status information as a dictionary.
        """

        response = {}
        for transfer_id, requests in requests_by_eid.items():
            for request_id in requests:
                with self.client_app() as client_app:
                    with self.transfer_client(client_app) as tc:
                        status = tc.get_task(request_id)

                response.setdefault(transfer_id, {})[request_id] = GlobusTransferStatusReport(request_id, transfer_id, status.get("status"))
        return response

    def bulk_update(self, resps, request_ids):
        pass

    def cancel(self):
        pass

    def update_priority(self):
        pass
