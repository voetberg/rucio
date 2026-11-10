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

from typing import Any, Optional

from flask import Flask, jsonify, request

from rucio.common import config
from rucio.common.constants import HTTPMethod
from rucio.common.exception import ConfigurationError, InvalidObject, InvalidPolicyPackageAlgorithmType
from rucio.common.plugins import PolicyPackageAlgorithms
from rucio.common.schema import validate_schema
from rucio.gateway.permission import has_permission
from rucio.web.rest.flaskapi.authenticated_bp import AuthenticatedBlueprint
from rucio.web.rest.flaskapi.v1.common import ErrorHandlingMethodView, check_accept_header_wrapper_flask, generate_http_error_flask, json_parameters, response_headers


def get_plugin(algo_name: str, algo_args: dict[str, Any], vo: str, issuer: Optional[str]) -> Any:

    if algo_name == "permission":
        return_value = has_permission(
            issuer=algo_args.get("issuer", issuer),
            action=algo_args["action"],
            kwargs=algo_args["extra_kwargs"],
            vo=vo
        )
        return bool(return_value)

    elif algo_name == "schema":
        try:
            validate_schema(
                name=algo_args["name"], obj=algo_args["obj"], vo=vo
            )
            return_value = True
        except InvalidObject:
            return_value = False
        return return_value

    else:
        algorithms = PolicyPackageAlgorithms()._get_algorithms(algo_name)
        if not algorithms:
            err = f"{algo_name} is not an accessable algorithm"
            raise InvalidPolicyPackageAlgorithmType(err)
        policy_algorithm = config.config_get('policy', algo_name, raise_exception=False)

        if policy_algorithm in algorithms.keys():
            result = algorithms[policy_algorithm](**algo_args)
        elif policy_algorithm is None:  # TODO Better fallback
            result = algorithms[list(algorithms.keys())[0]](**algo_args)
        else:
            err = f"{algo_name} with the policy {policy_algorithm} is not an accessable algorithm"
            raise ConfigurationError(err)

        return result


class Plugin(ErrorHandlingMethodView):

    @check_accept_header_wrapper_flask(['application/json'])
    def post(self, algo_name):
        """
        ---
        summary: Run a policy package algorithm
        description: |
          Generic entry point for invoking the server's policy package algorithms.
          The JSON body is passed as keyword arguments to the algorithm referenced
          by 'algo_name'. The reserved algorithm types 'permission' and 'schema'
          are routed to the permission and schema validators instead of the policy
          package. The algorithm used is the one configured in the 'policy' section
          of the Rucio configuration, or the first registered algorithm if none is
          configured.
        tags:
          - Plugin
        parameters:
        - name: algo_name
          in: path
          required: true
          schema:
            type: string
          description: "Name of the policy algorithm type to run (e.g. 'lfn2pfn', 'scope'), or one of the reserved types 'permission' and 'schema'."
        requestBody:
          content:
            'application/json':
              schema:
                type: object
                description: "Arguments forwarded to the algorithm as keyword arguments. The accepted fields depend on 'algo_name'; the fields below apply to the reserved algorithm types only."
                properties:
                  issuer:
                    description: "Account to check the permission for ('permission' only, defaults to the issuer of the authentication token)."
                    type: string
                  action:
                    description: "The action (API call) to check the permission for ('permission' only)."
                    type: string
                  extra_kwargs:
                    description: "Keyword arguments for the permission check ('permission' only)."
                    type: object
                  name:
                    description: "Name of the schema to validate against ('schema' only)."
                    type: string
                  obj:
                    description: "The object to validate against the schema ('schema' only)."
                    type: object
        responses:
          200:
            description: "Result of the algorithm. 'permission' and 'schema' return a JSON boolean (the outcome of the check), other algorithms return their result as JSON."
            content:
              application/json:
                schema:
                  description: "The value returned by the algorithm."
          400:
            description: "Cannot decode json parameter list, a required argument is missing, an argument is invalid, or the algorithm type is not available."
          406:
            description: "Not acceptable"
          500:
            description: "The server policy configuration references an algorithm which is not available."
        """
        # Perm and schema not explicitly included in plugins, route them separately

        vo = request.environ.get('vo', 'def')
        issuer = request.environ.get('issuer')
        args = json_parameters()
        try:
            return jsonify(get_plugin(algo_name, args, vo, issuer)), 200
        except KeyError as e:
            return generate_http_error_flask(400, 'MissingParameter', f'Missing argument {e}')
        except TypeError as e:
            return generate_http_error_flask(400, TypeError.__name__, str(e))
        except InvalidPolicyPackageAlgorithmType as e:
            return generate_http_error_flask(400, InvalidPolicyPackageAlgorithmType.__name__, str(e))
        except ConfigurationError as e:
            return generate_http_error_flask(500, InvalidPolicyPackageAlgorithmType.__name__, str(e))


def blueprint():
    bp = AuthenticatedBlueprint('plugin', __name__, url_prefix='/plugin')

    plugin_view = Plugin.as_view('plugin')
    bp.add_url_rule('/<algo_name>', view_func=plugin_view, methods=[HTTPMethod.POST.value])

    bp.after_request(response_headers)
    return bp


def make_doc():
    """ Only used for sphinx documentation to add the prefix """
    doc_app = Flask(__name__)
    doc_app.register_blueprint(blueprint())
    return doc_app
