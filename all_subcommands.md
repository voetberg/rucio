# rucio -h 
```
usage: rucio [-h] [--version] [--config CONFIG] [--verbose] [-H ADDRESS] [--auth-host ADDRESS] [-a ISSUER] [-S AUTH_STRATEGY] [-T TIMEOUT] [--user-agent USER_AGENT] [--vo VO] [-u USERNAME] [-pwd PASSWORD]
             [--oidc-user OIDC_USERNAME] [--oidc-password OIDC_PASSWORD] [--oidc-scope OIDC_SCOPE] [--oidc-audience OIDC_AUDIENCE] [--oidc-auto] [--oidc-polling]
             [--oidc-refresh-lifetime OIDC_REFRESH_LIFETIME] [--oidc-issuer OIDC_ISSUER] [--certificate CERTIFICATE] [--ca-certificate CA_CERTIFICATE]
             {account,config,did,replica,rse,rule,scope,subscription,ping,whoami,test-server,lifetime-exception} ...

positional arguments:
  {account,config,did,replica,rse,rule,scope,subscription,ping,whoami,test-server,lifetime-exception}
                        Command to execute, see `{command} -h` for more details and subcommands.

optional arguments:
  -h, --help            show this help message and exit

Main Arguments:
  --version             show program's version number and exit
  --config CONFIG       The Rucio configuration file to use.
  --verbose, -v         Print more verbose output.
  -H ADDRESS, --host ADDRESS
                        The Rucio API host.
  --auth-host ADDRESS   The Rucio Authentication host.
  -a ISSUER, --account ISSUER
                        Rucio account to use.
  -S AUTH_STRATEGY, --auth-strategy AUTH_STRATEGY
                        Authentication strategy (userpass, x509...)
  -T TIMEOUT, --timeout TIMEOUT
                        Set all timeout values to seconds.
  --user-agent USER_AGENT, -U USER_AGENT
                        Rucio User Agent
  --vo VO               VO to authenticate at. Only used in multi-VO mode.

Authentication Settings:
  -u USERNAME, --user USERNAME
                        username
  -pwd PASSWORD, --password PASSWORD
                        password
  --oidc-user OIDC_USERNAME
                        OIDC username
  --oidc-password OIDC_PASSWORD
                        OIDC password
  --oidc-scope OIDC_SCOPE
                        Defines which (OIDC) information user will share with Rucio. Rucio requires at least -sc="openid profile". To request refresh token for Rucio, scope must include "openid
                        offline_access" and there must be no active access token saved on the side of the currently used Rucio Client.
  --oidc-audience OIDC_AUDIENCE
                        Defines which audience are tokens requested for.
  --oidc-auto           If not specified, username and password credentials are not required and users will be given a URL to use in their browser. If specified, the users explicitly trust Rucio with their
                        IdP credentials.
  --oidc-polling        If not specified, user will be asked to enter a code returned by the browser to the command line. If --polling is set, Rucio Client should get the token without any further
                        interaction of the user. This option is active only if --auto is *not* specified.
  --oidc-refresh-lifetime OIDC_REFRESH_LIFETIME
                        Max lifetime in hours for this access token; the token will be refreshed by an asynchronous Rucio daemon. If not specified, refresh will be stopped after 4 days. This option is
                        effective only if --oidc-scope includes offline_access scope for a refresh token to be granted to Rucio.
  --oidc-issuer OIDC_ISSUER
                        Defines which Identity Provider is going to be used. The issuer string must correspond to the keys configured in the /etc/idpsecrets.json auth server configuration file.
  --certificate CERTIFICATE
                        Client certificate file.
  --ca-certificate CA_CERTIFICATE
                        CA certificate to verify peer against (SSL).
```
# account 
```
usage: rucio account [-h] [--type {GROUP,USER,SERVICE}] [-a ACCOUNT] [--id IDENTITY] [--filters FILTERS] {ban,attribute,limit,identity,list,add,info,remove,usage,set} ...

Default Operation: list
Methods to add or change accounts for users, groups, and services. Used to assign privileges.
Operations: ['list', 'add', 'info', 'remove', 'usage', 'set']
Subcommands: ['ban', 'attribute', 'limit', 'identity']

Usage Example:
$ rucio account  # List all accounts on the instance$ rucio account add --account user_jdoe --type USER  # Create a new user account
$ rucio account set --account user_jdoe --key email --value jdoe@cern.ch  # Update jdoe's email
$ rucio account usage --account root  # Show all the usage history for the account root

positional arguments:
  {ban,attribute,limit,identity,list,add,info,remove,usage,set}
    ban                 Disable an account. In case of accidental ban, use `$ rucio account ban remove`
    attribute           Add additional key/value pairs associated with an account for organizational purposes.
    limit               Manage storage limits for an account at a given RSE.
    identity            Manage identities (DNs) on an account.
    list                List accounts.
    add                 Add a new account.
    info                Get all stats on an account, including status, account type, and dates of creation and updates.
    remove              Delete an account.
    usage               See historical usage for an account
    set                 Change the basic account settings.

optional arguments:
  -h, --help            show this help message and exit
  --type {GROUP,USER,SERVICE}
                        Account Type
  -a ACCOUNT, --account ACCOUNT
                        Account name
  --id IDENTITY         Identity (e.g. DN)
  --filters FILTERS     Filter arguments in form `key=value,another_key=next_value`
```
 ## account ban 
```
rucio account ban -h 
usage: rucio account ban [-h] {add,remove} ...

Default Operation: add
Disable an account. In case of accidental ban, use `$ rucio account ban remove`
Operations: ['add', 'remove']
Subcommands: ['ban', 'attribute', 'limit', 'identity']

Usage Example:
$ rucio account ban add --account jdoe  # Ban jdoe
$ rucio account ban remove --account jdoe  # Un-Ban jdoe

positional arguments:
  {add,remove}
    add         Ban an account
    remove      Un-ban an account

optional arguments:
  -h, --help    show this help message and exit
```

## account attribute 
```
usage: rucio account attribute [-h] {list,add,remove} ...

Add additional key/value pairs associated with an account for organizational purposes.
Operations: ['list', 'add', 'remove']

Usage Example:
$ rucio account attribute list --account jdoe  # Show all attributes for jdoe
$ rucio -v account attribute add --account jdoe --key test_key --value true  # Set test_key = true for jdoe

positional arguments:
  {list,add,remove}
    list             List all account attributes.
    add              Add a new attribute to an account or update an existing one.
    remove           Remove an existing account attribute.

optional arguments:
  -h, --help         show this help message and exit
```
## account limit 
```
usage: rucio account limit [-h] {list,add,remove} ...

Manage storage limits for an account at a given RSE.
Operations: ['list', 'add', 'remove']

Usage Example:
$ rucio account  # List all accounts on the instance$ rucio account add --account user_jdoe --type USER  # Create a new user account
$ rucio account set --account user_jdoe --key email --value jdoe@cern.ch  # Update jdoe's email
$ rucio account usage --account root  # Show all the usage history for the account root

positional arguments:
  {list,add,remove}
    list             Show limits for an account at a given RSE.
    add              Add or update limits for an account.
    remove           Remove all limits for given account/rse/locality.

optional arguments:
  -h, --help         show this help message and exit
```

## account identity
```
usage: rucio account identity [-h] {list,add,remove} ...

Manage identities (DNs) on an account.
Operations: ['list', 'add', 'remove']

Usage Example:
$ rucio account identity list --account jdoe  # List all auth identities for jdoe
$ rucio account identity add --account jdoe --type GSS --email jdoe@cern.ch --id jdoe@fnal.ch  # Add a new GSS auth
$ rucio account identity add --account jdoe --type X509 --id 'CN=Joe Doe,CN=707658,CN=jdoe,OU=Users,OU=Organic Units,DC=cern,DC=ch' --email jdoe@cern.ch  # Add a new X509 auth. Note the DN in quotes.

positional arguments:
  {list,add,remove}
    list             Show existing DNs for an account.
    add              Grant identity access to an account. Format IDs as 'KEY1=Value One,KEY2=Value Two' if DNs.
    remove           Revoke identity access for an account.

optional arguments:
  -h, --help         show this help message and exit
```

# config 

```
usage: rucio config [-h] [-s SECTION] [-o OPTION] [-v VALUE] {list,set,remove} ...

Default Operation: list
Manage the global settings.
CAUTION: changing global configurations can have unintended consequences!
Operations: ['list', 'set', 'remove']

Usage Example:
 $ rucio config set --section limitsscratchdisk --option testlimit --value 30  # Change the existing limitstractdisk section
 $ rucio config list --section foo # Show the settings in section foo
 $ rucio config  # Show all the different sections of the config
 $ rucio config remove --section testsection -- option test  # Remove the value in testsection/test

positional arguments:
  {list,set,remove}
    list                Show the existing config.
    set                 Update the existing configuration settings. WARNING: Changes the global config.
    remove              Remove a setting from the configuration. WARNING: Changes the global config.

optional arguments:
  -h, --help            show this help message and exit
  -s SECTION, --section SECTION
                        Section name
  -o OPTION, --option OPTION
                        Option name
  -v VALUE, --value VALUE
                        String-encoded value
```

# DID 
```
usage: rucio did [-h] [--recursive] [--filter FILTER] [--short] [-d DID] {content,metadata,container,dataset,list,stat,remove,touch,parent,attach,detach,upload,download} ...

Default Operation: list
Manage Data IDentifiers. Modify and access specific files and groups of files. DIDs are accessed by the pattern `scope`:`name`, where name can be a wildcard, but scope must be specified.
Operations: ['list', 'stat', 'remove', 'touch', 'parent', 'attach', 'detach', 'upload', 'download']
Subcommands: ['content', 'metadata', 'container', 'dataset']

Usage Example:
$ rucio did --did user.jdoe:*  # Show all collection level DIDs with the scope user.jdoe
$ rucio did list --short --filter type=CONTAINER --did user.jdoe:* # Show the names of all container type DIDs
$ rucio did list --filter type=all --did user.jdoe:*  # Show all DIDs with the scope user.jdoe
$ rucio did remove --did user.jdoe:file_12345  # Disable file_12345. Will be deleted 24 after deletions.
$ rucio did touch --did user.jdoe:file_12345  # Update the time the DID has been modified
$ rucio did stat --did user.jdoe:file_12345  # Get the stats for file_12345 - account holder, size, expiration, open status, type, etc 
$ rucio did parent --did user.jdoe:file_12345 # Show all the parent DIDs for file_12345
$ rucio did attach --did user.jdoe:file_12345 --to user.jdoe:dataset_123  # Make dataset_123 the parent of file_12345
$ rucio did detach --did user.jdoe:file_12345 --from user.jdoe:datset_123  # Orphan file_12345

positional arguments:
  {content,metadata,container,dataset,list,stat,remove,touch,parent,attach,detach,upload,download}
    content             View the content of collection-type DIDs (datasets and containers), and update their open/closed status.
    metadata            Manage metadata attached to DIDs via a metadata plugin.
    container           Manage Containers (high-level grouping construct).
    dataset             Manage Datasets (mid-level grouping construct)
    list                List the Data IDentifiers matching certain pattern. Only collection type DIDs are returned by default, use --filter 'type=all' to return all.
    stat                List attributes and statuses about data identifiers.
    remove              Delete a DID. Can be recovered for up to 24 hours after deletion.
    touch               Touch one or more DIDs and set the last accessed date to the current date.
    parent              List all parent DIDs for a selected DID.
    attach              Attach a list of Data IDentifiers (file, dataset or container) to an other Data IDentifier (dataset or container).
    detach              Detach a list of Data Identifiers (file, dataset or container) from an other Data Identifier (dataset or container).
    upload              Upload a DID
    download            Download a DID

optional arguments:
  -h, --help            show this help message and exit
  --recursive           List data identifiers recursively.
  --filter FILTER       Filter arguments in form `key=value,another_key=next_value`. Valid keys are name, type.
  --short               Just dump the list of DIDs.
  -d DID, --did DID     Data IDentifier pattern.
```

## did content 
```
usage: rucio did content [-h] {list,history,close,open} ...

View the content of collection-type DIDs (datasets and containers), and update their open/closed status.
Operations: ['list', 'history', 'close', 'open']
Subcommands: ['content', 'metadata', 'container', 'dataset']

Usage Example:
$ rucio did content list --did user.jdoe:test12345  # Show the content of a collection-like DID
$ rucio did content history --did user.jdoe:test12345  # Show the history of a DID's content
$ rucio did content close --did user.jdoe:test12345  # Close a DID so it cannot have more content added
$ rucio did content open --did user.jdoe:test12345  # Open a DID to new attachments

positional arguments:
  {list,history,close,open}
    list                Show the contents of a collection-type DID.
    history             Show the content history of a collection-type DID, when DIDs were created, modified, or deleted.
    close               Set a collection-type DID to 'closed', so it cannot have more child DIDs added to it.
    open                Set a collection-type DID to 'open', so more DIDs may be added to it as children.

optional arguments:
  -h, --help            show this help message and exit
```

## did metadata 
```
usage: rucio did metadata [-h] {list,add,remove} ...

Manage metadata attached to DIDs via a metadata plugin.
Operations: ['list', 'add', 'remove']
Subcommands: ['content', 'metadata', 'container', 'dataset']

Usage Example:
$ rucio did metadata add --did user.jdoe:test12345 --key project --value MyShinyNewProject # Update the project field for the DID
$ rucio did metadata list --did user.jdoe:test1245  # Show all the metadata for a DID
$ rucio did metadata list --did user.jdoe:test1245 user.jdoe:test67890  # Show all the metadata for both test12345 and test67890

positional arguments:
  {list,add,remove}
    list             Show current metadata for a DID.
    add              Add new metadata for a DID.
    remove           Delete an existing metadata field for a DID.

optional arguments:
  -h, --help         show this help message and exit
```

## did container
```
usage: rucio did container [-h] {add} ...

Manage Containers (high-level grouping construct).
Operations: ['add']
Subcommands: ['content', 'metadata', 'container', 'dataset']

Usage Example:
$ rucio did container add --did user.jdoe:test.cont.1234.1 # Make a new container named test.cont.1234.1

positional arguments:
  {add}
    add       Create a new container

optional arguments:
  -h, --help  show this help message and exit
```

## did dataset
```
usage: rucio did dataset [-h] {add} ...

Manage Datasets (mid-level grouping construct)
Operations: ['add']
Subcommands: ['content', 'metadata', 'container', 'dataset']

Usage Example:
$ rucio did dataset add --did user.jdoe:user.jdoe.test.data.1234.1 # Create a new dataset

positional arguments:
  {add}
    add       Create a new dataset.

optional arguments:
  -h, --help  show this help message and exit
```

# replica 
```
usage: rucio replica [-h] [-d DIDS [DIDS ...]] [--protocols PROTOCOLS] [--all-states] [--pfns] [--domain DOMAIN] [--link LINK] [--missing] [--metalink] [--no-resolve-archives] [--sort SORT] [-r RSES]
                     {state,list,dataset,pfn,tombstone} ...

Default Operation: list
Interact with a Data IDentifier at a specific Rucio Service Element.
Operations: ['list', 'dataset', 'pfn', 'tombstone']
Subcommands: ['state']

Usage Example:
$ rucio replica --did user.jdoe:test_file  # Show all replicas for user.jdoe:test_file, with their pfn and rse.
$ rucio replica dataset --did user.jdoe:test_dataset  # Show all replicas for the dataset user.jdoe:test_dataset
$ 

positional arguments:
  {state,list,dataset,pfn,tombstone}
    state               Manage replica state.
    list                List the replicas of a DID and its PFNs.
    dataset             List replica datasets
    pfn                 Show the pfn for replicas of a DID
    tombstone           Add a tombstone which will mark the replica as ready for deletion by a reaper daemon

optional arguments:
  -h, --help            show this help message and exit
  -d DIDS [DIDS ...], --did DIDS [DIDS ...]
                        List of space separated data identifiers.
  --protocols PROTOCOLS
                        List of comma separated protocols. (i.e. https, root, srm).
  --all-states          To select all replicas (including unavailable ones). Also gets information about the current state of a DID in each RSE.
  --pfns                Show only the PFNs.
  --domain DOMAIN       Force the networking domain. Available options: wan, lan, all.
  --link LINK           Symlink PFNs with directory substitution. For example: rucio list-file-replicas --rse RSE_TEST --link /eos/:/eos/ scope:datasetname
  --missing             To list missing replicas at a RSE-Expression. Must be used with --rses option
  --metalink            Output available replicas as metalink.
  --no-resolve-archives
                        Do not resolve archives which may contain the files.
  --sort SORT           Replica sort algorithm. Available options: geoip (default), random
  -r RSES, --rse RSES   The RSE filter expression
```
## replica state
  ```
usage: rucio replica state [-h] {suspicious,quarantine,bad,temp-unavailable} ...

Manage replica state.
Operations: ['suspicious', 'quarantine', 'bad', 'temp-unavailable']
Subcommands: ['state']

Usage Example:
$ rucio replica state bad --files mock:test --rse RSE  # Declare the replica of did mock:test at RSE to be bad
$ rucio replica state temp-unavailable --files mock:test --rse RSE --duration 10 # Declare mock:test at RSE to be unavailable for 10 seconds.
$ rucio replica state quarantine --files mock:test --rse RSE  # Apply a quarantine to mock:test
$ rucio replica state suspicious --rse RSE  # Show all the suspicious replicas at RSE

positional arguments:
  {suspicious,quarantine,bad,temp-unavailable}
    suspicious          Show existing replicas marked as suspicious.
    quarantine          Quarantine replicas.
    bad                 Declare bad replicas.
    temp-unavailable    Declare temporary unavailable replicas,

optional arguments:
  -h, --help            show this help message and exit
```

# RSE 
```
usage: rucio rse [-h] [--rse RSES] {attribute,distance,protocol,limit,qos,list,info,remove,add,set} ...

Default Operation: list
Manage Rucio Storage Elements - the sites where Rucio can place and access data.
Operations: ['list', 'info', 'remove', 'add', 'set']
Subcommands: ['attribute', 'distance', 'protocol', 'limit', 'qos']

Usage Example:
$ rucio rse  # Show all current RSEs, can also access with `rucio rse list`
$ rucio rse list --rse 'deterministic=True' # Show all RSEs that match the RSE Expression 'deterministic=True'
$ rucio rse remove --rse RemoveThisRSE  # Disable an RSE by name
$ rucio rse add --rse CreateANewRSE  # add a new RSE named CreateANewRSE
$ rucio rse set --rse rse123456 --setting deterministic --value False  # Make an RSE Non-Deterministic

positional arguments:
  {attribute,distance,protocol,limit,qos,list,info,remove,add,set}
    attribute           Manage RSE Attributes as key/value pairs. CAUTION: the existing attributes can be overwritten.
    distance            Manage distances between RSEs. Used for determining efficiency of transfers from RSE to RSE via multihop operations.
    protocol            Manage RSE transfer and storage protocols. Use `$ rucio rse info` to view an RSE's existing protocols.
    limit               Manage storage size limits. Existing limits can be found with `$ rucio rse info`.
    qos                 I have no idea what this does and documentation doesn't help. It's dire out here.
    list                Show all RSEs.
    info                Show history of RSE usage (date created, date updated, etc)
    remove              Disable an RSE.
    add                 Create a new RSE.
    set                 Update an existing RSE.

optional arguments:
  -h, --help            show this help message and exit
  --rse RSES            RSE name or expression
```

## RSE attribute 
```
usage: rucio rse attribute [-h] {list,set,remove} ...

Manage RSE Attributes as key/value pairs. 
CAUTION: the existing attributes can be overwritten.
Operations: ['list', 'set', 'remove']

Usage Example:
$ rucio rse attribute list --rse ThisRSE  # Show all the attributes for a given RSE
$ rucio rse attribute list --rse ThisRSE --key name # Show all the attribute 'name' for a given RSE
$ rucio rse attribute add --rse ThisRSE --key given-attribute --value updated # Set the attribute 'given-attribute' to 'updated' for an RSE.

positional arguments:
  {list,set,remove}
    list             Show existing attributes for an RSE.
    set              Update an RSE's setting.
    remove           Wipe an RSE's setting.

optional arguments:
  -h, --help         show this help message and exit
```

## RSE distance 
```
usage: rucio rse distance [-h] {list,add,remove,set} ...

Manage distances between RSEs. Used for determining efficiency of transfers from RSE to RSE via multihop operations.
Operations: ['list', 'add', 'remove', 'set']

Usage Example:
$ rucio rse distance list --rse rse1 --destination rse2  # View the existing distance between rse1 and rse2
$ rucio rse distance remove --rse rse1 --destination rse2  # Remove an existing distance
$ rucio rse distance add --rse rse1 --destination rse2 --distance 10  # Add the distance between two rses that do not already have a distance
$ rucio rse distance set --rse rse1 --destination rse2 --distance 20  # Update an existing distance

positional arguments:
  {list,add,remove,set}
    list                Show distances between RSEs
    add                 Add or update a distance between RSEs.
    remove              Delete the distance between a pair of RSEs. The mandatory parameters are source and destination.
    set                 Update the distance between a pair of RSE that already have a distance between them.

optional arguments:
  -h, --help            show this help message and exit
```

## RSE Protocol 
```
usage: rucio rse protocol [-h] {add,remove} ...

Manage RSE transfer and storage protocols. Use `$ rucio rse info` to view an RSE's existing protocols.
Operations: ['add', 'remove']
Subcommands: ['attribute', 'distance', 'protocol', 'limit', 'qos']

Usage Example:
$ rucio rse protocol --hostname jdoes.test.org --scheme gsiftp --prefix '/atlasdatadisk/rucio/' --port 8443 --rse JDOE_DATADISK  # Add a new protocol on jdoe.test.org that uses gsiftp
$ rucio rse protocol remove --scheme gsiftp --rse JDOE_DATADISK # Remove the existing gsiftp protocol.

positional arguments:
  {add,remove}
    add         Create a new RSE transfer protocol.
    remove      Remove an existing RSE protocol.

optional arguments:
  -h, --help    show this help message and exit
```

## RSE Limit 
```
usage: rucio rse limit [-h] {add,remove} ...

Manage storage size limits. Existing limits can be found with `$ rucio rse info`.
Operations: ['add', 'remove']

Usage Example:
$ rucio rse limit add --rse XRD1 --name MinFreeSpace --value 10000
$ rucio rse limit --rse XRD3 --name MinFreeSpace

positional arguments:
  {add,remove}
    add         Add a storage limit.
    remove      Remove an existing storage limit

optional arguments:
  -h, --help    show this help message and exit 
```
## RSE QOS 
```
usage: rucio rse qos [-h] {list,add,remove} ...

I have no idea what this does and documentation doesn't help. It's dire out here.
Operations: ['list', 'add', 'remove']

Usage Example:
$ rucio rse qospolicy list --rse JDOE_DATADISK  # List QoS Policy for a given RSE
$ rucio rse qospolicy add --rse JDOE_DATADISK --policy SLOW_BUT_CHEAP  # Add a SLOW_BUT_CHEAP policy to the JDOE_DATADISK RSE
$ rucio rse qospolicy remove --rse  JDOE_DATADISK --policy SLOW_BUT_CHEAP  # Remove the same policy

positional arguments:
  {list,add,remove}
    list             Show existing QoS Policies
    add              Add a new policy
    remove           Remove Policy

optional arguments:
  -h, --help   
```

# Rule 
```
usage: rucio rule [-h] [-a RULE_ACCOUNT] [--activity ACTIVITY] [--rule-id RULE_ID] [--lifetime LIFETIME] [--locked] [--source-replica-expression SOURCE_REPLICA_EXPRESSION] [--comment COMMENT] [-d DID]
                  [--traverse] [--csv] [--file FILE] [--subscription ACCOUNT SUBSCRIPTION]
                  {add,remove,info,history,set,list} ...

Default Operation: list
Create rules that require a number of replicas at a defined set of remote Rucio Storage Elements (RSEs). Rules will initialize transfers between sites.
Operations: ['add', 'remove', 'info', 'history', 'set', 'list']

Usage Example:
$ rucio rule add -d user.jdoe:test_did --copies 2 --rse SPAINSITES  # Create a rule that requires two copies of a did limited to Spanish Cites.
$ rucio rule list --did user.jdoe:test_did  # show rules impacting a DID
$ rucio rule list --rule-id rule123456  # View a summary for an existing rule
$ rucio rule info --rule-id rule123456  # View a detailed overview for an existing rule.
$ rucio rule remove --rule-id rule123456  # Deactivate a rule
$ rucio rule set --rule-id rule123456 --suspend # Suspend the execution of a rule
$ rucio rule set --rule-id rule123456 --move --rse NewRSE # Copy an existing rule to a new RSE

positional arguments:
  {add,remove,info,history,set,list}
    add                 Add replication rule to define number of replicas at sites.
    remove              Delete a replication rule. Replicas created by the rule will not be impacted unless specified to do so.
    info                Retrieve information about a specific rule.
    history             List history of different replica rules impacting a DID
    set                 Update replication rule, can be used to move a rule from one RSE to another.
    list                List replication rules.

optional arguments:
  -h, --help            show this help message and exit
  -a RULE_ACCOUNT, --account RULE_ACCOUNT
                        The account of the rule
  --activity ACTIVITY   Activity to be used (e.g. User, Data Consolidation)
  --rule-id RULE_ID     The rule ID, for accessing an existing rule.
  --lifetime LIFETIME   Rule lifetime (in seconds)
  --locked              Set the rule to locked - [WHAT IS THE CONSEQUENCE?]
  --source-replica-expression SOURCE_REPLICA_EXPRESSION
                        RSE Expression for RSEs to be considered for source replicas
  --comment COMMENT     Comment about the replication rule
  -d DID, --did DID     DIDs to look for rules.
  --traverse            Traverse the did tree and search for rules affecting this did
  --csv                 Write output to a CSV.
  --file FILE           List associated rules of an affected file
  --subscription ACCOUNT SUBSCRIPTION
                        List by account and subscription name
```
# Scope 
```
usage: rucio scope [-h] [-a ACCOUNT] {list,add} ...

Default Operation: list
Manage scopes - A namespace partition generally used to separate common data from user data.
Operations: ['list', 'add']

Usage Example:
$ rucio scope add --scope user.jdoe --account jdoe  # Add a new scope, 'user.jdoe' for use with the account jdoe.
$ rucio scope --account jdoe  # List the existing scopes for account jdoe.

positional arguments:
  {list,add}
    list                Show existing scopes.
    add                 Create a new scope.

optional arguments:
  -h, --help            show this help message and exit
  -a ACCOUNT, --account ACCOUNT
                        Account name for filtering, attribution.
```

# Subscription 

```
usage: rucio subscription [-h] [--name NAME] [-a SUBS_ACCOUNT] [--filter FILTER] [--long] {list,set,add,touch} ...

Default Operation: list
Automate processing of specific rules, will create new rules on a schedule.
Operations: ['list', 'set', 'add', 'touch']

Usage Example:
$ rucio subscription add --lifetime 2 --account jdoe --priority 1 --name jdoes_txt_files_on_datadisk  # Create a new subscription to create new rules
$ rucio subscription --account jdoe # List subscriptions for jdoe's account. Shows rules created by this subscription.

positional arguments:
  {list,set,add,touch}
    list                List all active subscriptions.
    set                 Update an existing subscription.
    add                 Create a new subscription.
    touch               Reevaluate did for subscription.

optional arguments:
  -h, --help            show this help message and exit
  --name NAME           Subscription name, used to identify the subscription in the place of an ID.
  -a SUBS_ACCOUNT, --account SUBS_ACCOUNT
                        Account name
  --filter FILTER       DID filter (eg '{"scope": ["tests"], "project": ["data12_8TeV"]}')
  --long                Show extra subscription information, including creation and expiration dates.

```

# Lifetime-Exception 
```
usage: rucio lifetime-exception [-h] [-f INPUTFILE] [--reason REASON] [-x EXPIRATION] {add} ...

Default Operation: add
Manage Lifetime Exceptions (to make protections against deletion from reaper daemons).
Operations: ['add']

Usage Example:
$ rucio lifetime-exception --inputfile myfile.txt --reason 'Needed for my analysis' --expiration 2015-10-30  # Add exceptions for all DIDs listed in myfile.txt

positional arguments:
  {add}
    add

optional arguments:
  -h, --help            show this help message and exit
  -f INPUTFILE, --inputfile INPUTFILE
                        File where the list of datasets requested to be extended are located.
  --reason REASON       The reason for the extension.
  -x EXPIRATION, --expiration EXPIRATION
                        The expiration date format YYYY-MM-DD
```
