#!/bin/bash

# Create directories for CA, server, and client keys
mkdir -p ca server client

# Generate CA private key and certificate
if [[ ! -f ca/ca.key ]]; then
    echo "'ca.key' not found. Creating new Root CA"
    openssl req -x509 -nodes -newkey rsa:2048 -out ca/ca.crt -outform PEM -days 3650 -config openssl.cnf -keyout ca/ca.key -subj "/CN=lab-ca"
else
    echo "'ca.key' found. Using existing Root CA"
fi

# NETCONF SERVER
if [[ ! -f server/server.key ]]; then
    echo "'server/server.key. Creating new key pair"
    openssl genpkey -algorithm RSA -out server/server.key
    openssl req -new -key server/server.key -out server/server.csr -config openssl.cnf -subj "/CN=nc-server"
    openssl x509 -req -in server/server.csr -CA ca/ca.crt -CAkey ca/ca.key -out server/server.crt -CAcreateserial -days 365
else
    echo "'server.key' found. Using existing keypair"
fi


# NETCONF CLIENT
if [[ ! -f client/client.key ]]; then
    echo "'client/client.key' not found. Creating new key pair"
    openssl genpkey -algorithm RSA -out client/client.key
    openssl req -new -key client/client.key -out client/client.csr --extensions usr_cert -config openssl.cnf -subj "/CN=nc-client"
    openssl x509 -req -in client/client.csr -CA ca/ca.crt -CAkey ca/ca.key -out client/client.crt -CAcreateserial -days 365
else
    echo "'client.key' found. Using existing keypair"
fi

echo "Certificate Authority (CA), server, and client key pairs and certificates generated."

# copy crt to juniper box
# scp ca/ca.crt server/server.crt server/server.key lab@${NC_HOST}:/home/lab
