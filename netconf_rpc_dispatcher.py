#!/usr/bin/env python3
import argparse
import sys
import os
import logging
import ssl

from lxml import etree
from ncclient import manager, transport
from ncclient.operations.rpc import RPCReply, RPCError
from ncclient.operations.errors import TimeoutExpiredError

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

def dispatch_rpc(rpc_data: etree.Element, netconf_connection: transport.Session, disable_auto_lock_commit_unlock: bool = False) -> RPCReply:
    """Processes the XML RPC and return <rpc-reply> element."""
    # Inspect XML for '<rpc>' tag and remove
    if rpc_data.tag == 'rpc': rpc_data = list(rpc_data)[0]

    try:
        # <edit-config> operation
        if rpc_data.tag == 'edit-config' and not disable_auto_lock_commit_unlock:
            assert ":candidate" in netconf_connection.server_capabilities,"Candidate Configuration Capability not found"
            logging.info(f"Executing '<{rpc_data.tag}>' NETCONF operation")
            netconf_connection.lock(target='candidate')
            rpc_reply = netconf_connection.rpc(rpc_command=rpc_data)
            netconf_connection.commit()
            netconf_connection.unlock(target='candidate')

        # Other netconf operations
        # https://datatracker.ietf.org/doc/html/rfc6241#section-7
        # https://www.rfc-editor.org/rfc/rfc6022.html#section-3
        elif rpc_data.tag in [ 'edit-config', 'get', 'get-config', 'get-schema',
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
        logging.exception(etree.tostring(e.xml).decode('utf-8'))
        netconf_connection.close_session()
        sys.exit(1)

def process_rpc(rpc: str) -> etree.Element:
    """Read in list of RPCs from argparse --rpc option and transform them into XML objects"""
    if os.path.isfile(rpc):
        with open(rpc, "r") as file:
            rpc_data = file.read()
    else:
        rpc_data = rpc
    return etree.fromstring(rpc_data)


def main():
    parser = argparse.ArgumentParser(
        description="Generic NETCONF RPC Dispatcher",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    # NETCONF GENERIC OPTS
    nc_generic_parser = parser.add_argument_group('NETCONF Generic OPTIONS')
    nc_generic_parser.add_argument("--host", type=str, default='localhost', help="NETCONF server")
    nc_generic_parser.add_argument("--port", type=int, default=830, help="NETCONF server port")
    nc_generic_parser.add_argument("--transport", type=str, default="ssh", choices=["ssh", "tls"], help="NETCONF transport (ssh|tls)")

    # ADD RPC OPTS
    rpc_parser = parser.add_argument_group('RPC Input OPTIONS')
    rpc_parser.add_argument("--rpc",type=str, action="append", help="RPC XML data as FQPN (filename) or XML str. Read from STDIN if not provided...use Ctrl-D to signal EOF)")
    rpc_parser.add_argument("--timeout", type=int, default=60, help="RPC default response timeout in seconds")
    rpc_parser.add_argument("--disable-auto-lock-commit-unlock", action="store_true", help="Disable automatic locking, committing, and unlocking for edit-config operations")

    # NETCONF SSH OPTS
    nc_ssh_parser = parser.add_argument_group('SSH Transport OPTIONS')
    nc_ssh_parser.add_argument("--username", type=str, default='lab', help="SSH username")
    nc_ssh_parser.add_argument("--password", type=str, default='lab123', help="SSH password")
    nc_ssh_parser.add_argument("--ssh-key", type=str, default="~/.ssh/id_ecdsa", help="SSH private key")

    # NCCLIENT TLS OPTS
    nc_tls_parser = parser.add_argument_group('TLS Transport OPTIONS')
    nc_tls_parser.add_argument("--ca-certs", type=str, default='all_CAs', help="Path to the CA certificates file or directory")
    nc_tls_parser.add_argument("--certfile", type=str, default='client.crt', help="Path to the client certificate file (in PEM format)")
    nc_tls_parser.add_argument("--keyfile", type=str, default="client.key", help="Path to the client private key file (in PEM format)")
    # nc_tls_parser.add_argument("--tls-version", type=str, default="tlsv1_2", choices=["tlsv1_2", "tlsv1_3"], help="TLS version to use (either tlsv1_2 or tlsv1_3)")

    # NOTE:
    #   TLS connection paramters aren't referenced in the official ncclient 0.6.13 docs
    #   https://github.com/ncclient/ncclient/blob/master/ncclient/transport/tls.py#L67

    # ADD LOGGING OPTS
    logging_parser = parser.add_argument_group('Logging OPTIONS')
    logging_parser.add_argument("--log-file", type=str, default=None, help="Logging file")
    logging_parser.add_argument("--log-level", type=str, choices=["NOTSET", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], default="NOTSET", help="Logging level")

    # ARGUMENT PROCESSING
    args = parser.parse_args()
    setup_logger(args)

    logging.info("Starting NETCONF script")

    # RPC STR TO XML OBJECT CONVERSION
    # --rpc examples/get_config.xml
    # --rpc '<rpc><get-config><source><running/></source></get-config></rpc>'
    # echo '<rpc><get-config><source><running/></source></get-config></rpc>' | {PROGNAME} --host ${NC_HOST}

    xml_rpcs: list[etree.Element] = []

    if args.rpc:
        xml_rpcs += list(map(process_rpc, args.rpc))
    else:
        input_xml = sys.stdin.read().strip()
        xml_rpcs.append(etree.fromstring(input_xml))

    logging.info("Connecting to NETCONF server")
    if args.transport == 'ssh':
        nc_conn = manager.connect(
            host=args.host, port=args.port, username=args.username,
            password=args.password, key_filename=os.path.expanduser(args.ssh_key))
    elif args.transport == 'tls':
        nc_conn = manager.connect_tls(
            host=args.host,ca_certs=args.ca_certs,check_hostname=False,server_hostname=args.host,
            keyfile=args.keyfile, certfile=args.certfile, protocol=ssl.PROTOCOL_TLS_CLIENT, port=args.port)

    nc_conn.HUGE_TREE_DEFAULT=True
    nc_conn.timeout = args.timeout

    # DISPATCH RPC
    for rpc in xml_rpcs:
        rpc_reply = dispatch_rpc(rpc, nc_conn, args.disable_auto_lock_commit_unlock)
        sys.stdout.write(repr(rpc_reply) + '\n')

    nc_conn.close_session()
    logging.info("NETCONF script completed")

if __name__ == "__main__":
    main()
