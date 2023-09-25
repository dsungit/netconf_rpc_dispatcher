#!/usr/bin/env python3
import argparse
import sys
import os
import logging

from lxml import etree
from ncclient import manager, transport
from ncclient.operations.rpc import RPCReply, RPCError
from ncclient.operations.errors import TimeoutExpiredError 
from textwrap import dedent

PROGNAME=os.path.basename(__file__)

def setup_logger(args: argparse.Namespace):
    """Setup basic logging"""
    if args.log_level != 'NOTSET':
        logging.basicConfig(
           level=getattr(logging, args.log_level),
           format="%(asctime)s [%(levelname)s]: %(message)s",
           handlers=[
               logging.FileHandler(args.log_file) if args.log_file else logging.StreamHandler(),
           ]
        )

def establish_ncclient_connection(host: str, port: int, username: str, password: str, ssh_key: str) -> transport.Session:
    """Attempt to connect to NETCONF server via SSH and return connection handler"""
    connection = manager.connect(
        host=host, port=port, username=username,
        password=password, key_filename=ssh_key)
    return connection

def dispatch_rpc(rpc_data: etree.Element, netconf_connection: transport.Session) -> RPCReply:
    """Processes the XML RPC and return <rpc-reply> element."""
    # Inspect XML for '<rpc>' tag and remove
    if rpc_data.tag == 'rpc': rpc_data = list(rpc_data)[0]
    
    try:
        # <edit-config> operation
        if rpc_data.tag == 'edit-config':
            logging.info(f"Executing '<{rpc_data.tag}>' NETCONF operation")
            netconf_connection.lock(target='candidate')
            rpc_reply = netconf_connection.rpc(rpc_command=rpc_data)
            netconf_connection.commit()
            netconf_connection.unlock(target='candidate')

        # Other netconf operations
        # https://datatracker.ietf.org/doc/html/rfc6241#section-7
        # https://www.rfc-editor.org/rfc/rfc6022.html#section-3
        elif rpc_data.tag in [ 'get', 'get-config', 'get-schema', 
                'copy-config', 'delete-config', 'lock', 'unlock', 
                'close-session', 'kill-session' ] :
            logging.info(f"Executing '<{rpc_data.tag}>' NETCONF operation")
            rpc_reply = netconf_connection.rpc(rpc_command=rpc_data)
        
        # Generic RPC dispatch
        else:
            logging.info(f"Executing '<{rpc_data.tag}>' RPC")
            rpc_reply = netconf_connection.rpc(rpc_command=rpc_data)

        return rpc_reply

    except TimeoutExpiredError:
        # May want to add a retry or wait option for longer commits...just error out and exit for now
        logging.exception(TimeoutExpiredError)
        netconf_connection.close_session()
        sys.exit(1)
    except RPCError as e:
        logging.exception(e)
        netconf_connection.close_session()
        sys.exit(1)

def process_rpc(rpc: str):
    """
    Read in list of RPCs from argparse --rpc option and transform them into XML objects 
    """
    if os.path.isfile(rpc):
        with open(rpc, "r") as file:
            rpc_data = file.read()
    else:
        rpc_data = rpc

    return etree.fromstring(rpc_data)


def main():
    parser = argparse.ArgumentParser(
        description="Generic NETCONF RPC Dispatcher",
        epilog=dedent(f"""
        # RPC FROM STDIN (FILE)
        python3 {PROGNAME} --host r1.lab --log-level DEBUG <examples/jnpr/jnpr_edit_config.xml 

        # RPC FROM STDIN (SINGLE LINE)
        python3 {PROGNAME} --host r1.lab --log-level DEBUG <<< '<get-route-engine-information/>'

        # RPC FROM STDIN, REDIRECT STDERR TO STDOUT AND LOG
        python3 {PROGNAME} --host r1.lab --log-level DEBUG <examples/jnpr/jnpr_get_config.xml 2>&1 | tee session.log

        # MULTIPLE RPCS 
        python3 {PROGNAME} --host r1.lab --log-level DEBUG \\
            --rpc '<get-chassis-inventory/>'  \\
            --rpc 'examples/get_config.xml' \\
            --rpc '<rpc>
                       <get-interface-information>
                           <terse/>
                           <interface-name>et-0/0/0</interface-name>
                       </get-interface-information>
                   </rpc>'
        """),
        formatter_class=argparse.RawTextHelpFormatter)

    # ADD RPC OPTS
    parser.add_argument("--rpc",type=str, action="append", help="RPC XML data as FQPN (filename) or XML str. Read from STDIN if not provided...use Ctrl-D to signal EOF)")
    parser.add_argument("--timeout", type=int, default=60, help="RPC default response timeout in seconds")

    # ADD NCCLIENT OPTS
    parser.add_argument("--host", type=str, default='localhost', help="NETCONF server host")
    parser.add_argument("--port", type=int, default=830, help="NETCONF server port")
    parser.add_argument("--username", type=str, default='lab', help="NETCONF client username")
    parser.add_argument("--password", type=str, default='lab123', help="NETCONF client password")
    parser.add_argument("--ssh-key", type=str, default=os.path.expanduser("~/.ssh/id_ecdsa"), help="NETCONF client private SSH key")

    # ADD LOGGING OPTS
    parser.add_argument("--log-file", type=str, default=None, help="Logging file")
    parser.add_argument("--log-level", type=str, choices=["NOTSET", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], default="NOTSET", help="Logging level")

    # ARGUMENT PROCESSING
    args = parser.parse_args()
    setup_logger(args)

    # CONFIGURE LOGGING
    #if args.log_level != 'NOTSET':
    #   logging.basicConfig(
    #       level=getattr(logging, args.log_level),
    #       format="%(asctime)s [%(levelname)s]: %(message)s",
    #       handlers=[
    #           logging.FileHandler(args.log_file) if args.log_file else logging.StreamHandler(),
    #       ]
    #   )
    
    logging.info("Starting NETCONF script")

    # RPC STR TO XML OBJECT CONVERSION
    # --rpc examples/get_config.xml 
    # --rpc '<rpc><get-config><source><running/></source></get-config></rpc>'
    # echo '<rpc><get-config><source><running/></source></get-config></rpc>' | {PROGNAME} --host r1.lab 

    xml_rpcs: list[etree.Element] = []
    
    if args.rpc:
        xml_rpcs += list(map(process_rpc, args.rpc)) 
    else:
        input_xml = sys.stdin.read().strip()
        xml_rpcs.append(etree.fromstring(input_xml))

    logging.info("Connecting to NETCONF server")
    nc_conn = establish_ncclient_connection(
                    args.host, args.port, args.username,
                    args.password, args.ssh_key)

    nc_conn.timeout = args.timeout
    
    # DISPATCH RPC
    for rpc in xml_rpcs:
        rpc_reply = dispatch_rpc(rpc, nc_conn)
        sys.stdout.write(repr(rpc_reply) + '\n')

    nc_conn.close_session()

    logging.info("NETCONF script completed")

if __name__ == "__main__":
    main()
