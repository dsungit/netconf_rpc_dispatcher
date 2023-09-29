## OVERVIEW

This script ingests one or more generic NETCONF RPCs, dispatches the RPCs to a target NETCONF server, and outputs the RPC replies to STDOUT.

Its purpose is to enable network engineers and developers on my team to quickly and easily test new NETCONF and YANG configurations.

It can be used to:

* Test new NETCONF RPC operations by executing them on a remote NETCONF server.
* Test new YANG configurations by loading them onto a remote NETCONF server and identifying and fixing any errors.
* Develop and test NETCONF and YANG applications, such as a Python application that uses the nornir library to execute NETCONF RPCs on multiple devices.

For `<edit-config>` NETCONF operations, the script automatically locks/commits/unlocks the target configuration datastore. This behavior [can be disabled](#example-8---disable-auto-lock-commit-and-unlock) by using the `--disable-auto-lock-commit-unlock` option

Acceptable RPC input sources:
* STDIN
* --rpc `$XML_RPC_FILENAME` 
* --rpc `$XML_RPC_STRING`

While there are dedicated functions and helper routines available in `ncclient` library that simplify NETCONF operations from a development perspective, this script takes a more generalized approach for NETCONF RPC invocation. This allows developers to focus on properly modeling NETCONF XML RPC payloads, rather than getting tied down by specific library functions.

* Only NETCONF over SSH
* No NETCONF over TLS at this time
* Execute Multiple RPCs per session by invoking `--rpc` option multiple times

This script was tested against Juniper [vEVO](https://www.juniper.net/documentation/us/en/software/vJunosEvolved/vjunos-evolved-kvm/topics/vjunosevolved-understand.html) Routers

## REQUIREMENTS
* https://github.com/ncclient/ncclient


## USAGE

```bash
usage: netconf_rpc_dispatcher.py [-h] [--rpc RPC] [--timeout TIMEOUT] [--disable-auto-lock-commit-unlock] [--host HOST] [--port PORT] [--username USERNAME]
                                 [--password PASSWORD] [--ssh-key SSH_KEY] [--log-file LOG_FILE] [--log-level {NOTSET,DEBUG,INFO,WARNING,ERROR,CRITICAL}]

Generic NETCONF RPC Dispatcher

options:
  -h, --help            show this help message and exit
  --rpc RPC             RPC XML data as FQPN (filename) or XML str. Read from STDIN if not provided...use Ctrl-D to signal EOF) (default: None)
  --timeout TIMEOUT     RPC default response timeout in seconds (default: 60)
  --disable-auto-lock-commit-unlock
                        Disable automatic locking, committing, and unlocking for edit-config operations (default: False)
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

### Example 8 - Disable Auto Lock Commit and Unlock:
For `edit-config` operations, the script expects a candidate data store and will automatically lock, dispatch the RPC, commit, and unlock the target data store. The script expects a candidate data store because this allows for safe and controlled changes to the running configuration.

You can disable the automatic lock-commit-unlock behavior by using the `--disable-auto-lock-commit-unlock` option. This may be useful if you need to finer control over the RPC execution flow. 

In the example below, we want to use the `commit-confirmed` operation instead of the default `commit` operation to ensure that post-commit validation checks are run and that changes are automatically rolled back if the changes made result in loss of access to the device.

RUN A COMMIT-CONFIRMED OPERATION MANUALLY
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
	
RUN SOME POST COMMIT VALIDATION CHECK
```
# commit confirmed will be rolled back in 10 minutes
[edit class-of-service scheduler-maps]
root@vevo1# show | compare 
[edit class-of-service scheduler-maps SCH-MAP:NEBULA-TRANSIT]
-  forwarding-class Q1-EXPEDITED-FORWARDING scheduler 10PCT-EF;
+  forwarding-class Q1-EXPEDITED-FORWARDING scheduler 15PCT-EF;
```

COMMIT THE CHANGE
```bash
dysun@dysun-Super-Server:~/code/netconf_rpc_dispatcher$ python3 netconf_rpc_dispatcher.py --host 10.10.1.35 --rpc '<commit/>'
<nc:rpc-reply  xmlns:junos="http://xml.juniper.net/junos/23.1R0/junos" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="urn:uuid:06ee19d8-afc0-44f5-99e2-6341443a506c">
<nc:ok/>
</nc:rpc-reply>
```


## SAMPLE SCRIPT OUTPUT

### RAW

In this example, we dispatch the `<get-software-information/>` RPC twice via the CLI, and the output is provided without any formatting. The `ncclient` library automatically adds the `nc` namespace prefix to the `rpc-reply` tag in the XML output.

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
