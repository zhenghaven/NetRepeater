#!/bin/bash
openssl genrsa -out tmp/tls.key 2048
openssl req -new -key tmp/tls.key -out tmp/tls.csr
openssl x509 -req -days 3650 -in tmp/tls.csr -signkey tmp/tls.key -out tmp/tls.crt
