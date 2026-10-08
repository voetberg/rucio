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

from typing import TYPE_CHECKING, Any, Literal, Optional, Union

from rucio.common import config
from rucio.common.exception import DataIdentifierNotFound
from rucio.common.extra import import_extras
from rucio.common.types import InternalScope
from rucio.common.utils import extract_scope
from rucio.core.did_meta_plugins.did_meta_plugin_interface import DidMetaPlugin

EXTRA_MODULES = import_extras(['metacat'])

if EXTRA_MODULES['metacat']:
    from metacat.webapi import MetaCatClient, NotFoundError

if TYPE_CHECKING:
    from collections.abc import Iterator


class MetaCatPlugin(DidMetaPlugin):
    """
    Create a connection to an external MetaCat server

    Enable with Config.metadata.plugins = [..., "rucio.core.did_meta_plugins.metacat_met.MetaCatPlugin"]
    This plugin allows Rucio to search for DIDs based on metadata,
    including for use in setting rules

    Requirements config fields:
        * metadata.metacat_server_url
        * metadata.metacat_auth_server_url
        * metadata.metacat_max_concurrent_queries
        * metadata.metacat_token_file
        * metadata.metacat_timeout

    This plugin makes the assumption that MetaCat and Rucio have the same file name,
    and DIDs in Rucio have the same construction as MetaCat (e.g. namespace:name).


    """
    _plugin_name = "MetaCat"

    def __init__(
            self,
            server_url: Optional[str] = None,
            auth_server_url: Optional[str] = None,
            max_concurrent_queries: Optional[int] = 5,
            token_file: Optional[str] = None,
            timeout: Optional[Union[float, int]] = None,
            vo: str = 'def'
        ):

        super().__init__()
        if server_url is None:
            server_url = config.config_get("metadata", "metacat_server_url")
        if auth_server_url is None:
            auth_server_url = config.config_get("metadata", "metacat_auth_server_url")
        if max_concurrent_queries is None:
            max_concurrent_queries = config.config_get_int("metadata", "metacat_max_concurrent_queries")
        if token_file is None:
            token_file = config.config_get("metadata", "metacat_token_file")
        if timeout is None:
            timeout = config.config_get_float("metadata", "metacat_timeout")

        self.metacat_client = MetaCatClient(
            server_url=server_url,
            auth_server_url=auth_server_url,
            max_concurrent_queries=max_concurrent_queries,
            token_file=token_file,
            timeout=timeout
        )
        self.vo = vo

    def _did_to_metacat(self, scope: InternalScope, name: str) -> str:
        """Convert a scope/name pair to a metacat dataset"""
        # TODO: Replace with inverse extract_scope method required for consistency
        return f"{scope.external}:{name}"

    def _metacat_to_did(self, dataset: str) -> tuple[InternalScope, str]:
        """Convert a metacat dataset to a Rucio DID"""
        (scope, name) = extract_scope(dataset, vo=self.vo)
        return InternalScope(scope, vo=self.vo), name

    def get_metadata(self, scope: "InternalScope", name: str) -> dict:
        # Translate a scope, name to a DID in metacat, get the associated metadata
        metacat_did = self._did_to_metacat(scope, name)
        query_result: Optional[dict] = self.metacat_client.get_file(did=metacat_did)
        if query_result is not None:
            metadata = query_result.get("metadata", {})
        else:
            metadata = {}
        return metadata

    def set_metadata(self, scope: "InternalScope", name: str, key: str, value: str, recursive: bool = False, *, session: Any | None = None) -> None:
        self.set_metadata_bulk(scope, name, meta={key: value}, recursive=recursive, session=session)

    def set_metadata_bulk(self, scope: "InternalScope", name: str, meta: dict[str, Any], recursive: bool = False, *, session: Any | None = None) -> None:
        metacat_did = self._did_to_metacat(scope, name)

        if recursive:
            files = self.metacat_client.get_file(name=metacat_did)
            # Assumes the metacat DID has the same children as the rucio DID
            # Should be true according to the rucio policies....
            if files is not None:
                # Construct the bulk update
                children = files.get("children", {})  # List of FIDs
                fids = [{"fid": fid} for fid in children]
                for fid in fids:
                    self.metacat_client.update_file(meta, files=fid)

            else:
                msg = f"Could not set metadata for {metacat_did}. DID does not exist in metacat."
                raise DataIdentifierNotFound(msg)

        try:
            self.metacat_client.update_file(meta, did=metacat_did)
        except NotFoundError as e:
            msg = f"Could not set metadata for {metacat_did}, DID not found - {e}"
            raise DataIdentifierNotFound(msg)

    def delete_metadata(self, scope: "InternalScope", name: str, key: str, *, session: Any | None = None) -> None:
        return super().delete_metadata(scope, name, key, session=session)

    def _create_filters(self, filters: dict[str, Any], ignore_case: bool = False) -> str:
        for filter in filters:
            pass

    def list_dids(
        self,
        scope: "InternalScope",
        filters: dict[str, Any],
        did_type: Literal['collection'] | Literal['dataset'] | Literal['container'] | Literal['file'] = 'collection',
        ignore_case: bool = False,
        limit: int | None = None,
        offset: int | None = None,
        long: bool = False,
        recursive: bool = False,
        *,
        session: Any | None = None
    ) -> "Iterator[str | dict[str, Any]]":

        """
        dataset or files - Cannot be both
            - raise exceoptuib fir all
        Filter translation - "c-ish", don't use the filter translatiuon engine

        Recursive case - files [from dataset recursively]
        Cannot compare fieldnames to fieldnmaes (not important?)

        Use 'in' and 'not in' for lists
        "limit" is an accepted key temr
        """
        metacat_did_type = None
        if did_type in ['collection', 'dataset', 'container']:
            metacat_did_type = "dataset"
        elif did_type == 'file':
            metacat_did_type = 'file'

        if metacat_did_type is None:
            msg = f"Cannot create a metacat query from did_type {did_type}, use collection or file."
            raise ValueError(msg)

        if (offset is not None):
            # TODO log that this is not used
            pass

        query = metacat_did_type
        if recursive:
            query += ' [from dataset recursively]'
        else:
            query += ' from dataset'
        query += ' matching {scope.external}:"*" '

        query += self._create_filters(filters, ignore_case)

        if limit is not None:
            query += f"limit {limit}"
        meta = self.metacat_client.query(query, namespace=scope.external)
        return meta

    def manages_key(self, key: str, *, session: Any | None = None) -> bool:
        # Metacat can manage any DID, do not assume any field cannot exist or has already exists
        return True
