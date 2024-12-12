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
import argparse
from typing import TYPE_CHECKING

from rucio.client.commands.bin_legacy.rucio import upload
from rucio.client.commands.command_base import CommandBase
from rucio.common.config import config_get_float

if TYPE_CHECKING:
    from argparse import ArgumentParser

    from rucio.client.commands.utils import OperationDict


class Upload(CommandBase):
    def module_help(self) -> str:
        return "Upload DIDs"

    def parser(self, parser: "argparse._SubParsersAction[ArgumentParser]") -> None:

        command_parser = parser.add_parser(self.PARSER_NAME, description=self._help(), formatter_class=argparse.RawDescriptionHelpFormatter)

        command_parser.add_argument('--rse', '--rse_name', dest='rse', action='store', help='Rucio Storage Element (RSE) name.', required=True)
        command_parser.add_argument('--lifetime', type=int, action='store', help='Lifetime of the rule in seconds.')
        command_parser.add_argument('--expiration-date', action='store', help='The date when the rule expires in UTC, format: <year>-<month>-<day>-<hour>:<minute>:<second>. E.g. 2022-10-20-20:00:00')
        command_parser.add_argument('--scope', dest='scope', action='store', help='Scope name.')
        command_parser.add_argument('--impl', dest='impl', action='store', help='Transfer protocol implementation to use (e.g: xrootd, gfal.NoRename, webdav, ssh.Rsync, rclone).')
        # The --no-register option is hidden. This is pilot ONLY. Users should not use this. Will lead to unregistered data on storage!
        command_parser.add_argument('--no-register', dest='no_register', action='store_true', default=False, help=argparse.SUPPRESS)
        command_parser.add_argument('--register-after-upload', dest='register_after_upload', action='store_true', default=False, help='Register the file only after successful upload.')
        command_parser.add_argument('--summary', dest='summary', action='store_true', default=False, help='Create rucio_upload.json summary file')
        command_parser.add_argument('--guid', dest='guid', action='store', help='Manually specify the GUID for the file.')
        command_parser.add_argument('--protocol', action='store', help='Force the protocol to use')
        command_parser.add_argument('--pfn', dest='pfn', action='store', help='Specify the exact PFN for the upload.')
        command_parser.add_argument('--name', dest='name', action='store', help='Specify the exact LFN for the upload.')
        command_parser.add_argument('--transfer-timeout', dest='transfer_timeout', type=float, action='store', default=config_get_float('upload', 'transfer_timeout', False, 360), help='Transfer timeout (in seconds).')
        command_parser.add_argument(dest='args', action='store', nargs='+', help='files and datasets.')
        command_parser.add_argument('--recursive', dest='recursive', action='store_true', default=False, help='Convert recursively the folder structure into collections')

    def usage_example(self):
        return [
            "$ rucio upload [files1 file2 file3]  --rse MyRSE  # Upload files to a specific RSE",
            "$ rucio upload [files1 file2 file3]  --rse MyRSE  --register-after-upload # Upload files to a specific RSE, registering it automatically"
        ]

    def _operations(self) -> dict[str, "OperationDict"]:
        return {}

    def __call__(self):
        upload(self.args, self.client, self.logger, self.console, self.spinner)
