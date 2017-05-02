#!/bin/bash -e

#
# Bash example to remove a server/vm from the CoScale platform
#

BASE_URL=https://api.coscale.com
APP_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
ACCESS_TOKEN=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
SERVER=hostname

# Get an Authorization Token using the Access Token

TOKEN=`curl -s -X POST -d "accessToken=${ACCESS_TOKEN}" "${BASE_URL}/api/v1/app/${APP_ID}/login/"`
AUTH_TOKEN=`echo $TOKEN | python -c 'import sys, json; print json.load(sys.stdin)["token"]'`

# Get the server by name
SERVERS=`curl -s -H "HTTPAuthorization: ${AUTH_TOKEN}" ${BASE_URL}/api/v1/app/${APP_ID}/servers/?selectByName=${SERVER}`
SERVER_ID=`echo $SERVERS | python -c 'import sys, json; print json.load(sys.stdin)[0]["id"]'`

# Delete the server by id
curl -s -X DELETE -H "HTTPAuthorization: ${AUTH_TOKEN}" ${BASE_URL}/api/v1/app/${APP_ID}/servers/${SERVER_ID}/
