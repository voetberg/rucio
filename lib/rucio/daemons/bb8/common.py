# Copyright 2016-2018 CERN for the benefit of the ATLAS collaboration.
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
#
# Authors:
# - Martin Barisits <martin.barisits@cern.ch>, 2016-2017
# - Vincent Garonne <vgaronne@gmail.com>, 2016-2018
# - Tomas Javurek <tomas.javurek@cern.ch>, 2017
# - Cedric Serfon <cedric.serfon@cern.ch>, 2017

import logging
import sys

from datetime import datetime, date, timedelta

from rucio.core.lock import get_dataset_locks
from rucio.core.rule import get_rule, add_rule, update_rule
from rucio.core.rse_expression_parser import parse_expression
from rucio.core.rse import list_rse_attributes, get_rse_name
from rucio.core.rse_selector import RSESelector
from rucio.common.config import config_get
from rucio.common.exception import (InsufficientTargetRSEs, RuleNotFound, DuplicateRule,
                                    InsufficientAccountLimit)
from rucio.db.sqla.constants import RuleGrouping
from rucio.db.sqla.session import transactional_session


logging.basicConfig(stream=sys.stdout,
                    level=getattr(logging,
                                  config_get('common', 'loglevel',
                                             raise_exception=False,
                                             default='DEBUG').upper()),
                    format='%(asctime)s\t%(process)d\t%(levelname)s\t%(message)s')


def rebalance_rule(parent_rule, activity, rse_expression, priority, source_replica_expression=None, comment=None):
    """
    Rebalance a replication rule to a new RSE

    :param parent_rule:                Replication rule to be rebalanced.
    :param activity:                   Activity to be used for the rebalancing.
    :param rse_expression:             RSE expression of the new rule.
    :param priority:                   Priority of the newly created rule.
    :param source_replica_expression:  Source replica expression of the new rule.
    :param comment:                    Comment to set on the new rules.
    :returns:                          The new child rule id.
    """

    if parent_rule['expires_at'] is None:
        lifetime = None
    else:
        lifetime = (parent_rule['expires_at'] - datetime.utcnow()).days * 24 * 3600 + (parent_rule['expires_at'] - datetime.utcnow()).seconds

    if parent_rule['grouping'] == RuleGrouping.ALL:
        grouping = 'ALL'
    elif parent_rule['grouping'] == RuleGrouping.NONE:
        grouping = 'NONE'
    else:
        grouping = 'DATASET'

    # check if concurrent replica at target rse does not exist
    concurrent_replica = False
    try:
        for lock in get_dataset_locks(parent_rule['scope'], parent_rule['name']):
            if lock['rse'] == rse_expression:
                concurrent_replica = True
    except Exception as error:
        concurrent_replica = True
        print 'Exception: get_dataset_locks not feasible for %s %s:' % (parent_rule['scope'], parent_rule['name'])
        raise error
    if concurrent_replica:
        return 'Concurrent replica exists at target rse!'
    print concurrent_replica

    child_rule = add_rule(dids=[{'scope': parent_rule['scope'],
                                 'name': parent_rule['name']}],
                          account=parent_rule['account'],
                          copies=parent_rule['copies'],
                          rse_expression=rse_expression,
                          grouping=grouping,
                          weight=parent_rule['weight'],
                          lifetime=lifetime,
                          locked=parent_rule['locked'],
                          subscription_id=parent_rule['subscription_id'],
                          source_replica_expression=source_replica_expression,
                          activity=activity,
                          notify=parent_rule['notification'],
                          purge_replicas=parent_rule['purge_replicas'],
                          ignore_availability=False,
                          comment=parent_rule['comments'] if not comment else comment,
                          ask_approval=False,
                          asynchronous=False,
                          ignore_account_limit=True,
                          priority=priority)[0]

    update_rule(rule_id=parent_rule['id'], options={'child_rule_id': child_rule, 'lifetime': 0})
    return child_rule


def _list_rebalance_rule_candidates_dump(rse, mode=None):
    """
    Download dump to tmporary directory

    :param rse:          RSE of the source.
    :param mode:         Rebalancing mode.
    """

    from requests import get

    # get last sunday locks dump date:
    today = date.today()
    today_idx = (today.weekday() + 1) % 7
    sun = today - timedelta(today_idx)
    last_sunday_date = sun.strftime('%d-%m-%Y')

    # expected location of a dump for given rse
    dumps_location = config_get('bb8', 'dumps_location', raise_exception=False, default='http://rucio-analytix.cern.ch:8080/LOCKS/')
    rse_dump = '%sGetFileFromHDFS?date=%s&rse=%s' % (dumps_location, str(last_sunday_date), rse)

    # fetching the dump
    candidates = []
    rules = {}
    r = get(rse_dump, stream=True)
    if not r:
        print 'RSE dump not available: %s' % rse_dump
        return candidates

    # looping over the dump and selecting the rules
    for l in r.iter_lines():
        if l:
            file_scope, file_name, rule_id, rse_expression, account, file_size, state = l.split('\t')
            if rule_id not in rules:
                rule_info = {}
                try:
                    rule_info = get_rule(rule_id=rule_id)
                except Exception as e:
                    rules[rule_id] = {'state': 'DELETED'}
                    print e
                    continue
                rules[rule_id] = {'scope': rule_info['scope'],
                                  'name': rule_info['name'],
                                  'rse_expression': rse_expression,
                                  'subscription_id': rule_info['subscription_id'],
                                  'length': 1,
                                  'state': 'ACTIVE',
                                  'bytes': int(file_size)}
            elif rules[rule_id]['state'] == 'ACTIVE':
                rules[rule_id]['length'] += 1
                rules[rule_id]['bytes'] += int(file_size)

    # looping over agragated rules collected from dump
    for r_id in rules:
        if mode == 'decommission':  # other modes can be added later
            if rules[r_id]['state'] == 'DELETED':
                continue
            candidates.append((rules[r_id]['scope'],
                               rules[r_id]['name'],
                               r_id,
                               rules[r_id]['rse_expression'],
                               rules[r_id]['subscription_id'],
                               rules[r_id]['bytes'],
                               rules[r_id]['length']))
    return candidates


@transactional_session
def list_rebalance_rule_candidates(rse, mode=None, session=None):
    """
    List the rebalance rule candidates based on the agreed on specification

    :param rse:          RSE of the source.
    :param mode:         Rebalancing mode.
    :param session:      DB Session.
    """

    if mode is None:
        sql = """SELECT dsl.scope as scope, dsl.name as name, rawtohex(r.id) as rule_id, r.rse_expression as rse_expression, r.subscription_id as subscription_id, d.bytes as bytes, d.length as length FROM atlas_rucio.dataset_locks dsl JOIN atlas_rucio.rules r ON (dsl.rule_id = r.id) JOIN atlas_rucio.dids d ON (dsl.scope = d.scope and dsl.name = d.name)
WHERE
dsl.rse_id = atlas_rucio.rse2id(:rse) and
(r.expires_at > sysdate+60 or r.expires_at is NULL) and
r.created_at < sysdate-60 and
r.account IN ('panda', 'root', 'ddmadmin') and
r.state = 'O' and
r.copies = 1 and
r.did_type = 'D' and
r.child_rule_id is NULL and
d.bytes is not NULL and
d.is_open = 0 and
d.did_type = 'D' and
r.grouping IN ('D', 'A') and
1 = (SELECT count(*) FROM atlas_rucio.dataset_locks WHERE scope=dsl.scope and name=dsl.name and rse_id = dsl.rse_id) and
0 < (SELECT count(*) FROM atlas_rucio.dataset_locks WHERE scope=dsl.scope and name=dsl.name and rse_id IN (SELECT id FROM atlas_rucio.rses WHERE rse_type='TAPE'))
ORDER BY dsl.accessed_at ASC NULLS FIRST, d.bytes DESC"""  # NOQA
    elif mode == 'decommission':  # OBSOLETE
        sql = """SELECT r.scope, r.name, rawtohex(r.id) as rule_id, r.rse_expression as rse_expression, r.subscription_id as subscription_id, 0 as bytes, 0 as length FROM atlas_rucio.rules r
WHERE
r.id IN (SELECT rule_id FROM atlas_rucio.locks WHERE rse_id = atlas_rucio.rse2id(:rse) GROUP BY rule_id) and
r.state = 'O' and
r.child_rule_id is NULL"""  # NOQA

    if mode != 'decommission':
        return session.execute(sql, {'rse': rse}).fetchall()
    else:  # can be applied only for decommission since the dumps doesn't contain info from dids and rules tables.
        return _list_rebalance_rule_candidates_dump(rse, mode)


@transactional_session
def select_target_rse(parent_rule, current_rse, rse_expression, subscription_id, rse_attributes, other_rses=[], exclude_expression=None, force_expression=None, session=None):
    """
    Select a new target RSE for a rebalanced rule.

    :param parent_rule           rule that is rebalanced.
    :param current_rse:          RSE of the source.
    :param rse_expression:       RSE Expression of the source rule.
    :param subscription_id:      Subscription ID of the source rule.
    :param rse_attributes:       The attributes of the source rse.
    :param other_rses:           Other RSEs with existing dataset replicas.
    :param exclude_expression:   Exclude this rse_expression from being target_rses.
    :param force_expression:     Force a specific rse_expression as target.
    :param session:              The DB Session
    :returns:                    New RSE expression
    """

    if rse_attributes['type'] != 'DATADISK' and force_expression is None:
        print 'WARNING: dest RSE(s) has to be provided with --force-expression for rebalancing of non-datadisk RSES.'
        raise InsufficientTargetRSEs

    if exclude_expression:
        target_rse = '(%s)\\%s' % (exclude_expression, current_rse)
    else:
        target_rse = current_rse

    rses = parse_expression(expression=rse_expression, session=session)
    # if subscription_id:
    #     pass
    #     # get_subscription_by_id(subscription_id, session)
    if force_expression is not None:
        if parent_rule['grouping'] != RuleGrouping.NONE:
            rses = parse_expression(expression='(%s)\\%s' % (force_expression, target_rse), filter={'availability_write': True}, session=session)
        else:
            # in order to avoid replication of the part of distributed dataset not present at rabalanced rse -> rses in force_expression
            # this will be extended with development of delayed rule
            rses = parse_expression(expression='((%s)|(%s))\\%s' % (force_expression, rse_expression, target_rse), filter={'availability_write': True}, session=session)
    elif len(rses) > 1:
        # Just define the RSE Expression without the current_rse
        return '(%s)\\%s' % (rse_expression, target_rse)
    elif rse_attributes['tier'] is True or int(rse_attributes['tier']) == 1:
        # Tier 1 should go to another Tier 1
        rses = parse_expression(expression='(tier=1&type=DATADISK)\\%s' % target_rse, filter={'availability_write': True}, session=session)
    elif int(rse_attributes['tier']) == 2:
        # Tier 2 should go to another Tier 2
        rses = parse_expression(expression='(tier=2&type=DATADISK)\\%s' % target_rse, filter={'availability_write': True}, session=session)
    elif int(rse_attributes['tier']) == 3:
        # Tier 3 will go to Tier 2, since we don't have enough t3s
        rses = parse_expression(expression='(tier=2&type=DATADISK)\\%s' % target_rse, filter={'availability_write': True}, session=session)
    rseselector = RSESelector(account='ddmadmin', rses=rses, weight='freespace', copies=1, ignore_account_limit=True, session=session)
    return get_rse_name([rse_id for rse_id, _, _ in rseselector.select_rse(size=0, preferred_rse_ids=[], blacklist=other_rses)][0], session=session)


@transactional_session
def rebalance_rse(rse, max_bytes=1E9, max_files=None, dry_run=False, exclude_expression=None, comment=None, force_expression=None, mode=None, priority=3, source_replica_expression=None, session=None):
    """
    Rebalance data from an RSE

    :param rse:                        RSE to rebalance data from.
    :param max_bytes:                  Maximum amount of bytes to rebalance.
    :param max_files:                  Maximum amount of files to rebalance.
    :param dry_run:                    Only run in dry-run mode.
    :param exclude_expression:         Exclude this rse_expression from being target_rses.
    :param comment:                    Comment to set on the new rules.
    :param force_expression:           Force a specific rse_expression as target.
    :param mode:                       BB8 mode to execute (None=normal, 'decomission'=Decomission mode)
    :param priority:                   Priority of the new created rules.
    :param source_replica_expression:  Source replica expression of the new created rules.
    :param session:                    The database session.
    :returns:                          List of rebalanced datasets.
    """
    rebalanced_bytes = 0
    rebalanced_files = 0
    rebalanced_datasets = []
    rse_attributes = list_rse_attributes(rse=rse, session=session)

    print '***************************'
    print 'BB8 - Execution Summary'
    print 'Mode:    %s' % ('STANDARD' if mode is None else mode.upper())
    print 'Dry Run: %s' % (dry_run)
    print '***************************'

    print 'scope:name rule_id bytes(Gb) target_rse child_rule_id'

    for scope, name, rule_id, rse_expression, subscription_id, bytes, length in list_rebalance_rule_candidates(rse=rse, mode=mode):
        if force_expression is not None and subscription_id is not None:
            continue

        if rebalanced_bytes + bytes > max_bytes:
            continue
        if max_files:
            if rebalanced_files + length > max_files:
                continue

        try:
            rule = get_rule(rule_id=rule_id)
            other_rses = [r['rse_id'] for r in get_dataset_locks(scope, name, session=session)]
            # Select the target RSE for this rule
            try:
                target_rse_exp = select_target_rse(parent_rule=rule,
                                                   current_rse=rse,
                                                   rse_expression=rse_expression,
                                                   subscription_id=subscription_id,
                                                   rse_attributes=rse_attributes,
                                                   other_rses=other_rses,
                                                   exclude_expression=exclude_expression,
                                                   force_expression=force_expression,
                                                   session=session)
                # Rebalance this rule
                if not dry_run:
                    child_rule_id = rebalance_rule(parent_rule=rule,
                                                   activity='Data rebalancing',
                                                   rse_expression=target_rse_exp,
                                                   priority=priority,
                                                   source_replica_expression=source_replica_expression,
                                                   comment=comment)
                else:
                    child_rule_id = ''
            except (InsufficientTargetRSEs, DuplicateRule, RuleNotFound, InsufficientAccountLimit):
                continue
            print '%s:%s %s %d %s %s' % (scope, name, str(rule_id), int(bytes / 1E9), target_rse_exp, child_rule_id)
            if 'Concurrent' in str(child_rule_id):
                print str(child_rule_id)
                continue
            rebalanced_bytes += bytes
            rebalanced_files += length
            rebalanced_datasets.append((scope, name, bytes, length, target_rse_exp, rule_id, child_rule_id))
        except Exception as error:
            print 'Exception %s occured while rebalancing %s:%s, rule_id: %s!' % (str(error), scope, name, str(rule_id))
            raise error

    print 'BB8 is rebalancing %d Gb of data (%d rules)' % (int(rebalanced_bytes / 1E9), len(rebalanced_datasets))
    return rebalanced_datasets
