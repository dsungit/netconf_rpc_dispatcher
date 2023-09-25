## OVERVIEW
This script ingests one or more generic NETCONF RPCs, dispatches the RPCs, and outputs the RPC replies to STDOUT.

For `<edit-config>` NETCONF operations, the script automatically locks/commits/unlocks the target configuration datastore.

Acceptable RPC input sources:
* STDIN
* --rpc `$XML_RPC_FILENAME` 
* --rpc `$XML_RPC_STRING`

While there are dedicated functions and helper routines available in `ncclient` library that simplify NETCONF operations from a development perspective, this script takes a more generalized approach for NETCONF RPC invocation. 

* Only NETCONF over SSH
* No NETCONF over TLS at this time
* Execute Multiple RPCs per session by invoking `--rpc` option multiple times

## REQUIREMENTS
* https://github.com/ncclient/ncclient


## USAGE


```bash
usage: netconf_rpc_dispatcher.py [-h] [--rpc RPC] [--timeout TIMEOUT] [--host HOST] [--port PORT] [--username USERNAME]
                                 [--password PASSWORD] [--ssh-key SSH_KEY] [--log-file LOG_FILE]
                                 [--log-level {NOTSET,DEBUG,INFO,WARNING,ERROR,CRITICAL}]

Generic NETCONF RPC Dispatcher

options:
  -h, --help            show this help message and exit
  --rpc RPC             RPC XML data as FQPN (filename) or XML str. Read from STDIN if not provided...use Ctrl-D to signal EOF)
                        (default: None)
  --timeout TIMEOUT     RPC default response timeout in seconds (default: 60)
  --host HOST           NETCONF server host (default: localhost)
  --port PORT           NETCONF server port (default: 830)
  --username USERNAME   NETCONF client username (default: lab)
  --password PASSWORD   NETCONF client password (default: lab123)
  --ssh-key SSH_KEY     NETCONF client private SSH key (default: /home/dysun/.ssh/id_ecdsa)
  --log-file LOG_FILE   Logging file (default: None)
  --log-level {NOTSET,DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        Logging level (default: NOTSET)
```

### Example 1 - RPC from STDIN (file):
```bash
python3 netconf_rpc_dispatcher.py --host r1.lab --log-level DEBUG <examples/jnpr/jnpr_edit_config.xml
```

### Example 2 - RPC from STDIN (single line text):
```bash
python3 netconf_rpc_dispatcher.py --host r1.lab --log-level DEBUG <<< '<get-route-engine-information/>'
```

### Example 3 - RPC from STDIN (mult-line text):
```bash
cat << EOF | python3 netconf_rpc_dispatcher.py --host r1.lab --log-level DEBUG
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
python3 netconf_rpc_dispatcher.py --host r1.lab --log-level DEBUG --rpc examples/jnpr/jnpr_edit_config.xml
```

### Example 5 - Redirect STDERR to logfile:
```bash
python3 netconf_rpc_dispatcher.py --host r1.lab --log-level DEBUG <examples/jnpr/jnpr_get_config.xml 2> session.log
```

### Example 6 - Redirect STDERR to STDOUT and logfile:
```bash
python3 netconf_rpc_dispatcher.py --host r1.lab --log-level DEBUG <examples/jnpr/jnpr_get_config.xml 2>&1 | tee session.log
```
### Example 7 - Multiple RPCs:
```bash
python3 netconf_rpc_dispatcher.py --host r1.lab --log-level DEBUG \
    --rpc '<get-chassis-inventory/>'  \
    --rpc 'examples/get_config.xml'   \
    --rpc '<rpc>
               <get-interface-information>
                   <terse/>
                   <interface-name>et-0/0/0</interface-name>
               </get-interface-information>
           </rpc>'
```

## SAMPLE SCRIPT OUTPUT
```bash
dysun@dysun-Super-Server:~/code/netconf_rpc_dispatcher$ python3 netconf_rpc_dispatcher.py --host 10.10.1.35 --log-level NOTSET <<< '<get-route-engine-information/>'
<nc:rpc-reply  xmlns:junos="http://xml.juniper.net/junos/23.1R0/junos" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="urn:uuid:e17a62a1-f934-4370-8bcc-9e42ea70d7fb">
<route-engine-information xmlns="http://xml.juniper.net/junos/23.1R1.8-EVO/junos-chassis">
    <route-engine>
        <slot>0</slot>
        <mastership-state>Master</mastership-state>
        <mastership-priority>Master (default)</mastership-priority>
        <status>OK</status>
        <temperature junos:celsius="0">0 degrees C / 32 degrees F</temperature>
        <memory-dram-size>674 MB</memory-dram-size>
        <memory-installed-size>(5120 MB installed)</memory-installed-size>
        <memory-buffer-utilization>86</memory-buffer-utilization>
        <cpu-user>4</cpu-user>
        <cpu-background>0</cpu-background>
        <cpu-system>8</cpu-system>
        <cpu-interrupt>0</cpu-interrupt>
        <cpu-idle>87</cpu-idle>
        <cpu-user1>4</cpu-user1>
        <cpu-background1>0</cpu-background1>
        <cpu-system1>9</cpu-system1>
        <cpu-interrupt1>0</cpu-interrupt1>
        <cpu-idle1>85</cpu-idle1>
        <cpu-user2>4</cpu-user2>
        <cpu-background2>0</cpu-background2>
        <cpu-system2>9</cpu-system2>
        <cpu-interrupt2>0</cpu-interrupt2>
        <cpu-idle2>85</cpu-idle2>
        <cpu-user3>4</cpu-user3>
        <cpu-background3>0</cpu-background3>
        <cpu-system3>9</cpu-system3>
        <cpu-interrupt3>0</cpu-interrupt3>
        <cpu-idle3>84</cpu-idle3>
        <model>RE-JNP10001-36MR</model>
        <serial-number>BUILTIN</serial-number>
        <start-time junos:seconds="1695539580">2023-09-24 07:13:00 UTC</start-time>
        <up-time junos:seconds="51675">14 hours, 21 minutes, 15 seconds</up-time>
        <load-average-one>1.01</load-average-one>
        <load-average-five>1.28</load-average-five>
        <load-average-fifteen>1.20</load-average-fifteen>
    </route-engine>
</route-engine-information>
</nc:rpc-reply>
dysun@dysun-Super-Server:~/code/generic_ncclient$ 
```
