#!/bin/bash
set -euo pipefail

# GENERIC OPTIONS
PROGNAME=$(basename $0)
LOG_FILE=''

# NETCONF DEFAULTS
NC_HOST='localhost'
NC_PORT='830'
NC_TRANSPORT='ssh'
NC_TRANSPORT_OPTS=('ssh' 'tls')
NC_RPCS=()

# NETCONF SSH
NC_SSH_USERNAME='lab'
NC_SSH_PASSWORD='lab123'
NC_SSH_KEY='~/.ssh/id_ecdsa'

# NETCONF TLS
NC_TLS_KEY='client.key'
NC_TLS_CRT='client.crt'
NC_CA_CRT='all_CAs'
NC_TLS_VER='tls1_2' # see `man openssl-s_client` for valid TLS options

# NOTE: 
# Linux SSH client does not support NETCONF 1.1, so no methods have been implemented to deal with chunked framing
# https://github.com/libssh2/libssh2/blob/master/example/subsystem_netconf.c#L249

# JUNIPER TLS NOTES: 
# https://www.juniper.net/documentation/us/en/software/junos/netconf/topics/topic-map/netconf-tls-connection.html
# https://www.juniper.net/documentation/en_US/junos/topics/concept/netconf-tls-connection-overview.htm
# Junos devices do not support using Elliptic Curve Digital Signature Algorithm (ECDSA) keys in NETCONF sessions over TLS.
# The server listens for incoming NETCONF-over-TLS connections on TCP port 6513 (appears to be unconfigurable) 

# https://apps.juniper.net/feature-explorer/feature-info.html?fKey=11264&fn=Netconf%20over%20TLS
# Juniper NETCONF TLS implementation only supports TLS 1.2
# Juniper ACX 7024 may not support NETCONF over TLS (untested)

function die() {
    msg="$1"
    echo $msg >&2
    exit 1
}

function process_rpc() {
    # READ RPC FROM FILE OR STRING
    local rpc="$1"
    if [[ -f ${rpc} ]]; then
        rpc_data=$(<"${rpc}")
        NC_RPCS+=("$rpc_data")
    else
        NC_RPCS+=("$rpc")
    fi
}

function process_netconf_1_0() {
    # Will reference this function later if pretty print opt is required
    local rpc_replies=()
    IFS=']]>]]>' 

    # POP NETCONF HELLO MESSAGE
    NC_SERVER_HELLO="${rpc_replies[0]}"
    unset rpc_replies[0]
    rpc_replies=("${rpc_replies[@]}")
 
    for ((i = 0; i < ${#rpc_requests[@]}; i++)); do
        echo "RPC Request ${i}:"
        echo "${rpc_requests[i]}"
        echo "RPC Reply ${i}:"
        echo "${rpc_replies[i]}"
        echo "\n-----------------\n"
    done
}

function process_netconf_1_1() {
    # Linux SSH netconf subsystem client does not emit 1.1 capabilites
    die "NOT IMPLEMENTED"
}

function usage {
    cat << EOF
USAGE: ${PROGNAME} [OPTIONS]

DESCRIPTION:
    Generic NETCONF RPC dispatcher for Juniper devices

Generic OPTIONS:
 -h, --help                Show this help message and exit.
 --log-file FILE           Specify a log file for debugging. (Default: None)

NETCONF Generic OPTIONS:
 --host HOST               NETCONF server host. (Default: localhost)
 --port PORT               NETCONF server port. (Default: 830)
 --transport TRANSPORT     NETCONF transport protocol (ssh|tls). (Default: ssh)

RPC Input OPTIONS:
 --rpc FILE/STRING         NETCONF XML RPC as a FILE/STRING 
                           This option can be invoked multiple times to dispatch multiple RPCs
                           If omitted, the script will automatically read from STDIN.

SSH Transport OPTIONS:
 --ssh-username USERNAME   SSH client username. (Default: lab)
 --ssh-password PASSWORD   SSH client password. (Default: lab123)
 --ssh-key KEY             SSH client private key file. (Default: ~/.ssh/id_ecdsa)

TLS Transport OPTIONS:
 --ca-crt CERTIFICATE      Trusted CA certificates file.(Default: None)
 --tls-key KEY             TLS client private key file. (Default: client.key)
 --tls-crt CERTIFICATE     TLS client public key file.  (Default: client.crt)
 --tls-ver VERSION         TLS version to use. Refer to 'man openssl-s_client'
                           for valid TLS version options. (Default: tls1_2)
EXAMPLE:

# DEBUGGING
PS4='Line \${LINENO}: ' bash -x \\
${PROGNAME} --host \${NC_HOST} \\
    --ssh-username lab \\
    --ssh-key ~/.ssh/id_ecdsa \\
    <<< '<rpc><get-config><source><running/></source></get-config></rpc>'

# REGULAR SSH
${PROGNAME} --host \${NC_HOST} \\
    --ssh-username lab \\
    --ssh-key ~/.ssh/id_ecdsa \\
    <<< \${NC_RPCS[@]}

# REGULAR TLS
${PROGNAME} --host \${NC_HOST} --port \${NC_PORT} \\
        -CAfile \${NC_CA_CRT} \\
        -cert \${NC_TLS_CRT} \\
        -key \${NC_TLS_KEY} \\
        -\$NC_TLS_VER <<< \${NC_RPCS[@]}

EOF
}

# PROCESS ARGS
while [[ $# -gt 0 ]]; do
    case $1 in
        # GENERIC OPTIONS
        -h|--help)  usage; exit;;
        --log-file) die "Invalid option: '$1'. Use bash shell redirection instead";;
        --outform)  OUTFORM=$2;shift 2;;
        
        # NETCONF GENERIC OPTIONS
        --host)         NC_HOST=$2;shift 2;;
        --port)         NC_PORT=$2;shift 2;;
        --transport)    NC_TRANSPORT=$2;shift 2;;
        --rpc)          process_rpc $2;shift 2;;

        # SSH OPTIONS
        --ssh-username) NC_SSH_USERNAME=$2;shift 2;;
        --ssh-password) NC_SSH_PASSWORD=$2;shift 2;;
        --ssh-key)      NC_SSH_KEY=$2;shift 2;;
        
        # TLS OPTIONS
        --ca-crt)       NC_CA_CRT=$2;shift 2;;  # Mainly for lab
        --tls-key)      NC_TLS_KEY=$2;shift 2;;
        --tls-crt)      NC_TLS_CRT=$2;shift 2;;
        --tls-ver)      NC_TLS_VER=$2;shift 2;;

        # CATCH ALL
        *) usage; die "Invalid option: '$1'. Please check the options list and try again.";;
    esac
done

# VALIDATE OPTIONS
[[ ${NC_TRANSPORT_OPTS[@]}  =~ "${NC_TRANSPORT}" ]] || \
    die "Invalid --transport option: '${NC_TRANSPORT}'. Valid options: $(echo ${NC_TRANSPORT_OPTS[@]})"

# READ RPC FROM STDIN IF NO `--rpc` OPT IS SET 
[ ${#NC_RPCS[@]} -eq 0 ] && NC_RPCS+=$(cat)
([ ${#NC_RPCS[@]} -eq 0 ] ||  [[ "${NC_RPCS[@]}" =~ ^[[:space:]]*$ ]]) && die "Please input 1 or more NETCONF RPCs"

# DISPATCH RPCS
if [ ${NC_TRANSPORT} == 'ssh' ]; then
    ssh ${NC_SSH_USERNAME}@${NC_HOST} \
        -p ${NC_PORT} \
        -i ${NC_SSH_KEY} \
        -T -s netconf <<< ${NC_RPCS[@]}

elif [ ${NC_TRANSPORT} == 'tls' ]; then
    # https://serverfault.com/questions/1079475/is-there-any-way-to-get-openssl-s-client-to-read-from-stdin
    ssh -tt $USER@localhost \
    "openssl s_client -quiet -no_ign_eof -connect ${NC_HOST}:${NC_PORT} \
        -CAfile ${NC_CA_CRT} \
        -cert ${NC_TLS_CRT} \
        -key ${NC_TLS_KEY} \
        -$NC_TLS_VER" <<< ${NC_RPCS[@]}
fi
