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
  --ssh-key SSH_KEY     NETCONF client private SSH key (default: ~/.ssh/id_ecdsa)
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

### Example 3 - RPC from STDIN (multi-line text):
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

### RAW

In this example, we dispatch the `<get-software-information/>` RPC twice via the CLI, and the output is provided without any formatting. The `ncclient` library automatically adds the `nc` namespace prefix to the `rpc-reply` tag in the XML output."

```bash
dysun@dysun-Super-Server:~/code/netconf_rpc_dispatcher$ python3 netconf_rpc_dispatcher.py \
    --host 10.10.1.35 \
    --log-level WARNING \
    --rpc '<get-software-information/>' \
    --rpc '<get-software-information/>'
<nc:rpc-reply  xmlns:junos="http://xml.juniper.net/junos/23.1R0/junos" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="urn:uuid:a5b259da-d8d8-462c-aa6e-35499e6b6303">
<software-information>
    <host-name>vevo1</host-name>
    <product-model>ptx10001-36mr</product-model>
    <product-name>jnp10001-36mr</product-name>
    <junos-version>23.1R1.8-EVO</junos-version>
    <yocto-version>3.0.2</yocto-version>
    <kernel-version>5.2.60-yocto-standard-g3549735</kernel-version>
    <package-information>
        <name>junos-evo-install-ptx-fixed-x86-64-23.1R1.8-EVOI20230421141601-evo-builder-1</name>
        <comment>JUNOS-EVO OS 64-bit [junos-evo-install-ptx-fixed-x86-64-23.1R1.8-EVOI20230421141601-evo-builder-1]</comment>
    </package-information>
</software-information>
</nc:rpc-reply>
<nc:rpc-reply  xmlns:junos="http://xml.juniper.net/junos/23.1R0/junos" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="urn:uuid:2077f368-6fd4-41fe-beaf-63c97586edbc">
<software-information>
    <host-name>vevo1</host-name>
    <product-model>ptx10001-36mr</product-model>
    <product-name>jnp10001-36mr</product-name>
    <junos-version>23.1R1.8-EVO</junos-version>
    <yocto-version>3.0.2</yocto-version>
    <kernel-version>5.2.60-yocto-standard-g3549735</kernel-version>
    <package-information>
        <name>junos-evo-install-ptx-fixed-x86-64-23.1R1.8-EVOI20230421141601-evo-builder-1</name>
        <comment>JUNOS-EVO OS 64-bit [junos-evo-install-ptx-fixed-x86-64-23.1R1.8-EVOI20230421141601-evo-builder-1]</comment>
    </package-information>
</software-information>
</nc:rpc-reply>
dysun@dysun-Super-Server:~/code/netconf_rpc_dispatcher$ 
```



### FORMATTED WITH BASH

Next we surround the output with a single `root` tag, remove the `nc` namespace prefix, and modify the output to include a title above each rpc reply. 
```bash
dysun@dysun-Super-Server:~/code/netconf_rpc_dispatcher$ python3 netconf_rpc_dispatcher.py \
    --host 10.10.1.35 \
    --log-level WARNING \
    --rpc '<get-software-information/>' \
    --rpc '<get-software-information/>' | \
    sed -e '1i\<root>' -e '$a\</root>' -e 's/nc://g' | \
    xmllint --xpath '//rpc-reply' - | \
    awk '/<rpc-reply/{print "RPC REPLY " ++i} 1;/<\/rpc-reply>/{print ""}' | \
    sed '$d'
RPC REPLY 1
<rpc-reply xmlns:junos="http://xml.juniper.net/junos/23.1R0/junos" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="urn:uuid:94d23471-01c9-420e-91d1-082369df2108">
<software-information>
    <host-name>vevo1</host-name>
    <product-model>ptx10001-36mr</product-model>
    <product-name>jnp10001-36mr</product-name>
    <junos-version>23.1R1.8-EVO</junos-version>
    <yocto-version>3.0.2</yocto-version>
    <kernel-version>5.2.60-yocto-standard-g3549735</kernel-version>
    <package-information>
        <name>junos-evo-install-ptx-fixed-x86-64-23.1R1.8-EVOI20230421141601-evo-builder-1</name>
        <comment>JUNOS-EVO OS 64-bit [junos-evo-install-ptx-fixed-x86-64-23.1R1.8-EVOI20230421141601-evo-builder-1]</comment>
    </package-information>
</software-information>
</rpc-reply>

RPC REPLY 2
<rpc-reply xmlns:junos="http://xml.juniper.net/junos/23.1R0/junos" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="urn:uuid:3a81e34d-c183-47d7-b2d9-eed52f49dc37">
<software-information>
    <host-name>vevo1</host-name>
    <product-model>ptx10001-36mr</product-model>
    <product-name>jnp10001-36mr</product-name>
    <junos-version>23.1R1.8-EVO</junos-version>
    <yocto-version>3.0.2</yocto-version>
    <kernel-version>5.2.60-yocto-standard-g3549735</kernel-version>
    <package-information>
        <name>junos-evo-install-ptx-fixed-x86-64-23.1R1.8-EVOI20230421141601-evo-builder-1</name>
        <comment>JUNOS-EVO OS 64-bit [junos-evo-install-ptx-fixed-x86-64-23.1R1.8-EVOI20230421141601-evo-builder-1]</comment>
    </package-information>
</software-information>
</rpc-reply>
dysun@dysun-Super-Server:~/code/netconf_rpc_dispatcher$
```

### FORMATTED WITH PYTHON

Here we do the same thing with python.

```python
from lxml import etree

# XML with a single root element
input_xml = """
<root>
    <nc:rpc-reply  xmlns:junos="http://xml.juniper.net/junos/23.1R0/junos" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="urn:uuid:d5fe9127-47ec-4cdb-af50-2fe18808d309">
    <software-information>
        <host-name>vevo1</host-name>
        <product-model>ptx10001-36mr</product-model>
        <product-name>jnp10001-36mr</product-name>
        <junos-version>23.1R1.8-EVO</junos-version>
        <yocto-version>3.0.2</yocto-version>
        <kernel-version>5.2.60-yocto-standard-g3549735</kernel-version>
        <package-information>
            <name>junos-evo-install-ptx-fixed-x86-64-23.1R1.8-EVOI20230421141601-evo-builder-1</name>
            <comment>JUNOS-EVO OS 64-bit [junos-evo-install-ptx-fixed-x86-64-23.1R1.8-EVOI20230421141601-evo-builder-1]</comment>
        </package-information>
    </software-information>
    </nc:rpc-reply>
    <nc:rpc-reply  xmlns:junos="http://xml.juniper.net/junos/23.1R0/junos" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="urn:uuid:f36521c5-fc7f-4804-a230-5bb5b0ebc1f9">
    <software-information>
        <host-name>vevo1</host-name>
        <product-model>ptx10001-36mr</product-model>
        <product-name>jnp10001-36mr</product-name>
        <junos-version>23.1R1.8-EVO</junos-version>
        <yocto-version>3.0.2</yocto-version>
        <kernel-version>5.2.60-yocto-standard-g3549735</kernel-version>
        <package-information>
            <name>junos-evo-install-ptx-fixed-x86-64-23.1R1.8-EVOI20230421141601-evo-builder-1</name>
            <comment>JUNOS-EVO OS 64-bit [junos-evo-install-ptx-fixed-x86-64-23.1R1.8-EVOI20230421141601-evo-builder-1]</comment>
        </package-information>
    </software-information>
    </nc:rpc-reply>
</root>
"""

# Parse the corrected input XML
root = etree.fromstring(input_xml)

# Find all <nc:rpc-reply> elements
rpc_reply_elements = root.xpath('//nc:rpc-reply', namespaces={'nc' : 'urn:ietf:params:xml:ns:netconf:base:1.0'})

# Loop through the <rpc-reply> elements and serialize them individually
for i, rpc_reply_element in enumerate(rpc_reply_elements, start=1):
    individual_xml = etree.tostring(rpc_reply_element, pretty_print=True, encoding='unicode')
    print(f"Individual XML {i}:\n{individual_xml}\n")
```

Python Script output

```python
>>> # Loop through the <rpc-reply> elements and serialize them individually
>>> for i, rpc_reply_element in enumerate(rpc_reply_elements, start=1):
...     individual_xml = etree.tostring(rpc_reply_element, pretty_print=True, encoding='unicode')
...     print(f"Individual XML {i}:\n{individual_xml}\n")
... 
Individual XML 1:
<nc:rpc-reply xmlns:junos="http://xml.juniper.net/junos/23.1R0/junos" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="urn:uuid:d5fe9127-47ec-4cdb-af50-2fe18808d309">
    <software-information>
        <host-name>vevo1</host-name>
        <product-model>ptx10001-36mr</product-model>
        <product-name>jnp10001-36mr</product-name>
        <junos-version>23.1R1.8-EVO</junos-version>
        <yocto-version>3.0.2</yocto-version>
        <kernel-version>5.2.60-yocto-standard-g3549735</kernel-version>
        <package-information>
            <name>junos-evo-install-ptx-fixed-x86-64-23.1R1.8-EVOI20230421141601-evo-builder-1</name>
            <comment>JUNOS-EVO OS 64-bit [junos-evo-install-ptx-fixed-x86-64-23.1R1.8-EVOI20230421141601-evo-builder-1]</comment>
        </package-information>
    </software-information>
    </nc:rpc-reply>
    


Individual XML 2:
<nc:rpc-reply xmlns:junos="http://xml.juniper.net/junos/23.1R0/junos" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="urn:uuid:f36521c5-fc7f-4804-a230-5bb5b0ebc1f9">
    <software-information>
        <host-name>vevo1</host-name>
        <product-model>ptx10001-36mr</product-model>
        <product-name>jnp10001-36mr</product-name>
        <junos-version>23.1R1.8-EVO</junos-version>
        <yocto-version>3.0.2</yocto-version>
        <kernel-version>5.2.60-yocto-standard-g3549735</kernel-version>
        <package-information>
            <name>junos-evo-install-ptx-fixed-x86-64-23.1R1.8-EVOI20230421141601-evo-builder-1</name>
            <comment>JUNOS-EVO OS 64-bit [junos-evo-install-ptx-fixed-x86-64-23.1R1.8-EVOI20230421141601-evo-builder-1]</comment>
        </package-information>
    </software-information>
    </nc:rpc-reply>
```
