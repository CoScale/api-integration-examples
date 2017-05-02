#!/usr/bin/env python

#
# Python example on how to create a CoScale application, create and agent and deploy it on a Kubernetes env
#


import requests
import argparse
import json

class CoScaleAPI:

    def __init__(self, baseurl, email, password):
        self.__baseurl = baseurl
        self.__email = email
        self.__password = password
        self.__token = None

    def login(self):
        ''' Login to the API, sets the token on the CoScaleAPI instance. '''
        response = requests.post('%s/api/v1/users/login/' % self.__baseurl, data={'email':self.__email, 'password':self.__password})
        js = response.json()
        if 'token' in js:
            self.__token = js['token']
        else:
            raise Exception('Invalid credentials')

    def get_auth_header(self):
        return {'HTTPAuthorization' : self.__token}

    def get_current_user(self):
        ''' Get the current user. '''
        response = requests.get('%s/api/v1/users/byEmail/%s/' % (self.__baseurl, self.__email) , headers=self.get_auth_header())
        return response.json()

    def new_application(self, owner_id, name):
        ''' Create a new application with the provided name and owner. '''
        response = requests.post('%s/api/v1/app/global/' % self.__baseurl, data={'ownerId':owner_id, 'name':name}, headers=self.get_auth_header())
        return response.json()

    def new_agent(self, app_id, name, os):
        ''' Create a new agent on an existing applications. '''
        data = {
            'name':name,
            'description':name,
            'os':os
        }
        response = requests.post('%s/api/v1/app/%s/agenttemplates/' % (self.__baseurl, app_id), data=data, headers=self.get_auth_header())
        return response.json()

    def add_plugin_to_agent(self, app_id, agent_id, plugin_type, config):
        ''' Add a plugin to an existing agent. '''
        data = {
            'pluginType':plugin_type,
            'config':config
        }
        response = requests.post('%s/api/v1/app/%s/agenttemplates/%d/plugins/' % (self.__baseurl, app_id, agent_id), data=data, headers=self.get_auth_header())
        return response.json()

    def get_kube_install_instructions(self, app_id, agent_id):
        cert = requests.get('%s/api/v1/app/%s/agenttemplates/CERT/' % (self.__baseurl, app_id), headers=self.get_auth_header()).json()['CERT']
        access_token = requests.get('%s/api/v1/app/%s/agenttemplates/%d/?expand=accesstoken' % (self.__baseurl, app_id, agent_id), headers=self.get_auth_header()).json()['accesstoken']['token']

        return '''
cat <<EOF | kubectl apply -f -
apiVersion: extensions/v1beta1
kind: DaemonSet
metadata:
  labels:
    name: coscale-agent
  name: coscale-agent
spec:
  template:
    metadata:
      labels:
        name: coscale-agent
    spec:
      hostNetwork: true    
      containers:
      - image: coscale/coscale-agent
        imagePullPolicy: Always
        name: coscale-agent
        env:
        - name: APP_ID
          value: "%s"
        - name: ACCESS_TOKEN
          value: "%s"
        - name: TEMPLATE_ID
          value: "%d"
        - name: BASE_URL
          value: "%s"
        - name: CERTIFICATE
          value: "%s"
        volumeMounts:
        - name: dockersocket
          mountPath: /var/run/docker.sock
        - name: hostroot
          mountPath: /host
          readOnly: true
      volumes:
      - hostPath:
          path: /var/run/docker.sock
        name: dockersocket
      - hostPath:
          path: /
        name: hostroot
EOF
''' % (app_id, access_token, agent_id, self.__baseurl, cert)


def main():
    """ The main function. """
    parser = argparse.ArgumentParser(description='Tool to integrate CoScale application creation.')
    parser.add_argument('-b', '--baseurl', dest='baseurl', required=True, help='the base url (eg https://api.coscale.com)')
    parser.add_argument('-e', '--email', dest='email', required=True, help='the CoScale super user email')
    parser.add_argument('-p', '--password', dest='password', required=True, help='the CoScale super user password')
    args = parser.parse_args()

    cs = CoScaleAPI(args.baseurl, args.email, args.password)
    cs.login()

    user = cs.get_current_user()
    app = cs.new_application(user['id'], 'New application')

    print 'Created new application: %s/app/%s/datasources/agents/' % (args.baseurl, app['appId'])

    agent = cs.new_agent(app['appId'], 'Kubernetes agent', 'KUBERNETES')
    cs.add_plugin_to_agent(app['appId'], agent['id'], 'RESOURCES', '{}')
    cs.add_plugin_to_agent(app['appId'], agent['id'], 'DOCKER', '{"MANAGED PLUGINS":["[]"]}')
    cs.add_plugin_to_agent(app['appId'], agent['id'], 'KUBERNETES', '{"HOSTNAME":["localhost"]}')

    print cs.get_kube_install_instructions(app['appId'], agent['id'])


if __name__ == '__main__':
    main()
