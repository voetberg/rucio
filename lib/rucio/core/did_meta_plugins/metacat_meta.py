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

from itertools import islice
from typing import TYPE_CHECKING, Any, Literal, Optional, Union

from rucio.common import config
from rucio.common.exception import DataIdentifierNotFound
from rucio.common.extra import import_extras
from rucio.common.types import InternalScope
from rucio.common.utils import extract_scope
from rucio.core.did_meta_plugins.did_meta_plugin_interface import DidMetaPlugin

EXTRA_MODULES = import_extras(['metacat'])

if EXTRA_MODULES['metacat']:
    from metacat.webapi import MetaCatClient
    from metacat.webapi.webapi import NotFoundError


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
        """
        Convert a scope/name pair to a metacat dataset

        Note: All metacat instances assume a "namespace":"name" format.
        """
        return f"{scope.external}:{name}"

    def _metacat_to_did(self, dataset: str) -> tuple[InternalScope, str]:
        """Convert a metacat dataset to a Rucio DID"""
        (scope, name) = extract_scope(dataset, vo=self.vo)
        return InternalScope(scope, vo=self.vo), name

    def get_metadata(self, scope: "InternalScope", name: str) -> dict:
        # Translate a scope, name to a DID in metacat, get the associated metadata
        metadata = {}
        metacat_did = self._did_to_metacat(scope, name)
        query_result: Optional[dict] = self.metacat_client.get_file(did=metacat_did)
        if query_result is not None:
            metadata = query_result.get("metadata", {})
        else:
            query_result: Optional[dict] = self.metacat_client.get_dataset(did=metacat_did)
            if query_result is not None:
                metadata = query_result.get("metadata", {})
        return metadata

    def set_metadata(self, scope: "InternalScope", name: str, key: str, value: str, recursive: bool = False, *, session: Optional[Any] = None) -> None:
        """Set one metadata field"""
        self.set_metadata_bulk(scope, name, meta={key: value}, recursive=recursive, session=session)

    def set_metadata_bulk(self, scope: "InternalScope", name: str, meta: dict[str, Any], recursive: bool = False, *, session: Optional[Any] = None) -> None:
        """
        Set multiple metadata fields.

        Note that the 'recursive' option requires that a Dataset is passed, and this dataset's
        metadata is also updated.
        """

        metacat_did = self._did_to_metacat(scope, name)

        if recursive:
            try:
                files = self.metacat_client.get_dataset_files(did=metacat_did)
                file_specs = [f for f in files]
            except NotFoundError as e:
                msg = f"Could not set metadata for {metacat_did}'s children DID, DID not found - {e}. \
                    Verify your DID is a dataset."
                raise DataIdentifierNotFound(msg)

            # Assumes the metacat DID has the same children as the rucio DID
            # Should be true according to the rucio policies...
            if len(file_specs) != 0:
                self.metacat_client.update_dataset(metacat_did, metadata=meta)
                self.metacat_client.update_file_meta(metadata=meta, files=file_specs)
            else:
                msg = f"Could not set metadata recursively for {metacat_did}. DID does not exist in metacat."
                raise DataIdentifierNotFound(msg)
        else:
            try:
                # Need to check if the did is a file or dataset, to call the correct method
                try:
                    self.metacat_client.update_file(metadata=meta, did=metacat_did)
                except NotFoundError:
                    self.metacat_client.update_dataset(metadata=meta, dataset=metacat_did)
            except NotFoundError as e:
                msg = f"Could not set metadata for {metacat_did}, DID not found - {e}"
                raise DataIdentifierNotFound(msg)

    def delete_metadata(self, scope: "InternalScope", name: str, key: str, *, session: Optional[Any] = None) -> None:
        """
        Remove a metadata value from a DID.
        Does not delete the key, just assigns it to None.
        """

        metacat_did = self._did_to_metacat(scope, name)
        if self.metacat_client.get_file(did=metacat_did) is not None:
            self.metacat_client.update_file(metacat_did, metadata={key: None})
        elif self.metacat_client.get_dataset(did=metacat_did) is not None:
            self.metacat_client.update_dataset(metacat_did, metadata={key: None})
        else:
            msg = f"Could not find {metacat_did} in MetaCat."
            raise DataIdentifierNotFound(msg)

    def _format_mql_literal(self, value: Any) -> str:
        if isinstance(value, str):
            escaped_value = value.replace('"', '\\"')
            return f'"{escaped_value}"'

        if isinstance(value, bool):
            return "true" if value else "false"

        if isinstance(value, (int, float)):
            return str(value)

        msg = f"Cannot translate metadata filter value of type {type(value)} into MQL"
        raise ValueError(msg)

    def _create_filters(self, filters: dict[str, Any], ignore_case: bool = False) -> str:
        """Translate rucio metadata filters into an MQL where-clause predicate, empty string when no filters."""
        if ignore_case:
            # TODO: Correct with MQL ~* operator
            msg = "MetaCat plugin does not support case-insensitive filters"
            raise NotImplementedError(msg)

        predicates: list[str] = []

        for filter_key, filter_value in filters.items():
            if isinstance(filter_value, dict):
                msg = f"Operator dictionaries are not supported in metacat filters: {filter_key}={filter_value}"
                raise NotImplementedError(msg)

            if isinstance(filter_value, (list, tuple, set)):
                rendered_values = ", ".join(self._format_mql_literal(single_value) for single_value in filter_value)
                predicates.append(f"{filter_key} in ({rendered_values})")
            else:
                predicates.append(f"{filter_key} == {self._format_mql_literal(filter_value)}")

        return " and ".join(predicates)

    def list_dids(
        self,
        scope: "InternalScope",
        filters: dict[str, Any],
        did_type: Literal['all', 'collection', 'dataset', 'container', 'file'] = 'collection',
        ignore_case: bool = False,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        long: bool = False,
        recursive: bool = False,
        *,
        session: Optional[Any] = None
    ) -> "Iterator[Union[str, dict[str, Any]]]":

        """
        List DIDs in a scope by running an MQL query against the connected MetaCat server.

        Please note MetaCat does not have a concept of containers, and all containers
        in Rucio are typically mapped to datasets. If you want to search for a container,
        it will return a MetaCat dataset, which may or may not be a container in Rucio.

        File queries match all active files in the namespace, or, when recursive, the
        files that are members of the datasets in the namespace. Dataset queries list
        datasets in the namespace, with metadata filters applied via the MQL 'having'
        clause; recursive dataset listings are not supported.
        """
        metacat_did_type = None
        if did_type in ['collection', 'dataset', 'container']:
            metacat_did_type = "dataset"
        elif did_type == 'file':
            metacat_did_type = 'file'

        if metacat_did_type is None:
            msg = f"Cannot create a metacat query from did_type {did_type}, use collection or file."
            raise ValueError(msg)

        filter_predicates = self._create_filters(filters, ignore_case)

        if metacat_did_type == 'file':
            if recursive:
                dataset_records = self.metacat_client.query(f"datasets matching {scope.external}:%", namespace=scope.external)
                dataset_specs = ", ".join(f"{dataset_record['namespace']}:{dataset_record['name']}" for dataset_record in dataset_records)

                if not dataset_specs:
                    return iter(())

                query = f"files from {dataset_specs}"
                if filter_predicates:
                    query += f" where {filter_predicates}"
            else:
                where_clauses = [f'namespace == "{scope.external}"']
                if filter_predicates:
                    where_clauses.append(filter_predicates)
                query = "files where " + " and ".join(where_clauses)

            if limit is not None:
                query += f" limit {limit}"
            if offset is not None:
                query += f" skip {offset}"

            query_result = self.metacat_client.query(query, namespace=scope.external)
            did_names = (file_record["name"] for file_record in query_result)

        else:
            if recursive:
                msg = "MetaCat plugin does not support recursive dataset listings"
                raise NotImplementedError(msg)

            query = f"datasets matching {scope.external}:%"
            if filter_predicates:
                query += f" having {filter_predicates}"

            query_result = self.metacat_client.query(query, namespace=scope.external)
            did_names = (dataset_record["name"] for dataset_record in query_result)

            if offset is not None:
                did_names = islice(did_names, offset, None)
            if limit is not None:
                did_names = islice(did_names, limit)

        if long:
            return ({"scope": scope, "name": did_name} for did_name in did_names)

        return did_names

    def manages_key(self, key: str, *, session: Optional[Any] = None) -> bool:
        # Metacat can manage any DID, do not assume any field cannot exist or has already exists
        return True
