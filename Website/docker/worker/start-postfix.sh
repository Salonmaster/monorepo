#!/bin/sh
postmap lmdb:/etc/postfix/sasl_passwd
postfix  start-fg
