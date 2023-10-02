## OVERVIEW

This script ingests one or more generic NETCONF RPCs, dispatches the RPCs to a target NETCONF server, and outputs the RPC replies to STDOUT.

Its purpose is to enable network engineers and developers to quickly and easily test new NETCONF and YANG configurations.

It can be used to:

* Test new NETCONF RPC operations by executing them on a remote NETCONF server.
* Test new YANG configurations by loading them onto a remote NETCONF server and identifying and fixing any errors.
* Develop and test NETCONF and YANG applications

For `<edit-config>` NETCONF operations, the script automatically locks/commits/unlocks the target configuration datastore. This behavior [can be disabled](#example-8---disable-auto-lock-commit-and-unlock) by using the `--disable-auto-lock-commit-unlock` option

Acceptable RPC input sources:
* STDIN
* --rpc `$XML_RPC_FILENAME` 
* --rpc `$XML_RPC_STRING`

While there are dedicated functions and helper routines available in the `ncclient 0.6.13` python library that simplify NETCONF operations from a development perspective, this script takes a more generalized approach for NETCONF RPC invocation.

Notes:
* Only NETCONF over SSH
* No NETCONF over TLS at this time
* Execute Multiple RPCs per session by invoking `--rpc` option multiple times

This script was tested against Juniper [vEVO](https://www.juniper.net/documentation/us/en/software/vJunosEvolved/vjunos-evolved-kvm/topics/vjunosevolved-understand.html) Routers

## REQUIREMENTS
* https://github.com/ncclient/ncclient


## USAGE

```bash
usage: netconf_rpc_dispatcher.py [-h] [--host HOST] [--port PORT] [--transport {ssh,tls}] [--rpc RPC] [--timeout TIMEOUT] [--disable-auto-lock-commit-unlock]
                                 [--username USERNAME] [--password PASSWORD] [--ssh-key SSH_KEY] [--ca-certs CA_CERTS] [--certfile CERTFILE] [--keyfile KEYFILE]
                                 [--tls-version {tlsv1_2,tlsv1_3}] [--log-file LOG_FILE] [--log-level {NOTSET,DEBUG,INFO,WARNING,ERROR,CRITICAL}]

Generic NETCONF RPC Dispatcher

options:
  -h, --help            show this help message and exit

NETCONF Generic OPTIONS:
  --host HOST           NETCONF server (default: localhost)
  --port PORT           NETCONF server port (default: 830)
  --transport {ssh,tls}
                        NETCONF transport (ssh|tls) (default: ssh)

RPC Input OPTIONS:
  --rpc RPC             RPC XML data as FQPN (filename) or XML str. Read from STDIN if not provided...use Ctrl-D to signal EOF) (default: None)
  --timeout TIMEOUT     RPC default response timeout in seconds (default: 60)
  --disable-auto-lock-commit-unlock
                        Disable automatic locking, committing, and unlocking for edit-config operations (default: False)

SSH Transport OPTIONS:
  --username USERNAME   SSH username (default: lab)
  --password PASSWORD   SSH password (default: lab123)
  --ssh-key SSH_KEY     SSH private key (default: ~/.ssh/id_ecdsa)

TLS Transport OPTIONS:
  --ca-certs CA_CERTS   Path to the CA certificates file or directory (default: all_CAs)
  --certfile CERTFILE   Path to the client certificate file (in PEM format) (default: client.crt)
  --keyfile KEYFILE     Path to the client private key file (in PEM format) (default: client.key)
  --tls-version {tlsv1_2,tlsv1_3}
                        TLS version to use (either tlsv1_2 or tlsv1_3) (default: tlsv1_2)

Logging Options:
  --log-file LOG_FILE   Logging file (default: None)
  --log-level {NOTSET,DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        Logging level (default: NOTSET)
```

### Example 1 - RPC from STDIN (file):
```bash
python3 netconf_rpc_dispatcher.py --host ${NC_HOST} \
    --log-level DEBUG <examples/jnpr/jnpr_edit_config.xml
```

### Example 2 - RPC from STDIN (single line text):
```bash
python3 netconf_rpc_dispatcher.py --host ${NC_HOST} \
    --log-level DEBUG <<< '<get-route-engine-information/>'
```

### Example 3 - RPC from STDIN (multi-line text):
```bash
cat << EOF | python3 netconf_rpc_dispatcher.py --host ${NC_HOST} --log-level DEBUG
<rpc>
    <get-config>
        <source>
            <running/>
        </source>
    </get-config>
</rpc>
EOF
```

### Example 4 - RPC from file via the '--rpc' option:
```bash
python3 netconf_rpc_dispatcher.py --host ${NC_HOST} \
    --log-level DEBUG --rpc examples/jnpr/jnpr_edit_config.xml
```

### Example 5 - Redirect STDERR to logfile:
```bash
python3 netconf_rpc_dispatcher.py --host ${NC_HOST} \
    --log-level DEBUG <examples/jnpr/jnpr_get_config.xml 2> session.log
```

### Example 6 - Redirect STDERR to STDOUT and logfile:
```bash
python3 netconf_rpc_dispatcher.py --host ${NC_HOST} \
    --log-level DEBUG <examples/jnpr/jnpr_get_config.xml 2>&1 | \
    tee session.log
```
### Example 7 - Multiple RPCs:
```bash
python3 netconf_rpc_dispatcher.py --host ${NC_HOST} --log-level DEBUG \
    --rpc '<get-chassis-inventory/>'  \
    --rpc 'examples/get_config.xml'   \
    --rpc '<rpc>
               <get-interface-information>
                   <terse/>
                   <interface-name>et-0/0/0</interface-name>
               </get-interface-information>
           </rpc>'
```

### Example 8 - Disable Auto Lock Commit and Unlock:
For `edit-config` operations, the script expects a candidate data store and will automatically lock, dispatch the RPC, commit, and unlock the target data store. The script expects a candidate data store because this allows for safe and controlled changes to the running configuration.

You can disable the automatic lock-commit-unlock behavior by using the `--disable-auto-lock-commit-unlock` option. This may be useful if you need to finer control over the RPC execution flow. 

In the example below, we want to use the `commit-confirmed` operation instead of the default `commit` operation to ensure that post-commit validation checks are run and that changes are automatically rolled back if the changes made result in loss of access to the device.

**RUN A COMMIT-CONFIRMED OPERATION MANUALLY**
```bash
dysun@dysun-Super-Server:~/code/netconf_rpc_dispatcher$ python3 netconf_rpc_dispatcher.py --host 10.10.1.35 --disable-auto-lock-commit-unlock \
        --rpc examples/lock.xml \
        --rpc examples/jnpr/jnpr_edit_config.xml \
        --rpc '<commit><confirmed/></commit>' \
        --rpc examples/unlock.xml
<nc:rpc-reply  xmlns:junos="http://xml.juniper.net/junos/23.1R0/junos" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="urn:uuid:f0d7401f-a116-4e8e-8995-dcd8db98fd53">
<nc:ok/>
</nc:rpc-reply>
<nc:rpc-reply  xmlns:junos="http://xml.juniper.net/junos/23.1R0/junos" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="urn:uuid:9bbbfc3e-a53a-4a0b-a6d2-c93b33f32e62">
<nc:ok/>
</nc:rpc-reply>
<nc:rpc-reply  xmlns:junos="http://xml.juniper.net/junos/23.1R0/junos" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="urn:uuid:b3bd4c46-1654-4572-982a-ed267944b7ae">
<nc:ok/>
</nc:rpc-reply>
<nc:rpc-reply  xmlns:junos="http://xml.juniper.net/junos/23.1R0/junos" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="urn:uuid:c03a910e-30b5-44fc-bae5-3fddcd392888">
<nc:ok/>
</nc:rpc-reply>
dysun@dysun-Super-Server:~/code/netconf_rpc_dispatcher$ 
```
	
**RUN SOME POST COMMIT VALIDATION CHECK**
```
# commit confirmed will be rolled back in 10 minutes
[edit class-of-service scheduler-maps]
root@vevo1# show | compare 
[edit class-of-service scheduler-maps SCH-MAP:NEBULA-TRANSIT]
-  forwarding-class Q1-EXPEDITED-FORWARDING scheduler 10PCT-EF;
+  forwarding-class Q1-EXPEDITED-FORWARDING scheduler 15PCT-EF;
```

**COMMIT THE CHANGE**
```bash
dysun@dysun-Super-Server:~/code/netconf_rpc_dispatcher$ python3 netconf_rpc_dispatcher.py --host 10.10.1.35 --rpc '<commit/>'
<nc:rpc-reply  xmlns:junos="http://xml.juniper.net/junos/23.1R0/junos" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="urn:uuid:06ee19d8-afc0-44f5-99e2-6341443a506c">
<nc:ok/>
</nc:rpc-reply>
```
