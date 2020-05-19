# Another LDAP authentication

**LDAP Authentication** for **Nginx**, **Kubernetes ingress controller** (Nginx), **HAProxy** ([haproxy-auth-request](https://github.com/TimWolla/haproxy-auth-request)) or any webserver/reverse proxy with authorization based on the result of a subrequest.

**Another LDAP Authentication** is an implementation of the `ldap-auth-daemon` services described in the official blog from Nginx in the [following article](https://www.nginx.com/blog/nginx-plus-authenticate-users/).

**Another LDAP Authentication** it's prepared to run inside a Docker container, also you can run the Python script without the Docker container. Supports `ldap` and `ldaps` and provide a simple cache.

## Diagram
![Another LDAP Authentication](https://i.ibb.co/Fn1ncbP/another-ldap-authentication.jpg)

## Installation and configuration
The easy way to use **Another LDAP Authentication** is running as a Docker container and set the parameters via environment variables.

### Step 1 - Run as a Docker container
Change the environment variables with your setup.

```
docker run -d \
        -e LDAP_ENDPOINT='ldaps://testmyldap.com:636' \
        -e LDAP_MANAGER_DN_USERNAME='CN=john-service-user,OU=Administrators,DC=TESTMYLDAP,DC=COM' \
        -e LDAP_MANAGER_PASSWORD='MasterpasswordNoHack123' \
        -e LDAP_SERVER_DOMAIN='TESTMYLDAP.COM' \
        -e LDAP_SEARCH_BASE='DC=TESTMYLDAP,DC=COM' \
        -e LDAP_SEARCH_FILTER='(sAMAccountName={username})' \
        -p 9000:9000 \
        --name another_ldap_auth \
        dignajar/another-ldap-auth:latest
```

**Another LDAP Authentication** now is running on `http://localhost:9000`.

### Step 2 - Nginx configuration
Nginx use the module [ngx_http_auth_request_module](http://nginx.org/en/docs/http/ngx_http_auth_request_module.html) to do the subrequest.

The following example shows how to configure Nginx which is running in the same machine as **Another LDAP Authentication**. The backend `/private/` includes the authentication request to `/another_ldap_auth`.

```
location /private/ {
    auth_request /another_ldap_auth;
    # ...
    # Here you private site
}

location = /another_ldap_auth {
    internal;
    proxy_pass_request_body off;
    proxy_set_header Content-Length "";
    proxy_pass http://localhost:9000;
}
```

## Deploy in Kubernetes with Nginx ingress controller

Another LDAP Auth deployment manifest, `another-deployment.yaml`.
```
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: another-ldap-auth
  namespace: ingress-nginx
  labels:
    app: another-ldap-auth
spec:
  replicas: 1
  selector:
    matchLabels:
      app: another-ldap-auth
  template:
    metadata:
      labels:
        app: another-ldap-auth
    spec:
      containers:
        - image: dignajar/another-ldap-auth:latest
          name: another-ldap-auth
          ports:
            - name: http
              containerPort: 9000
          env:
            - name: LDAP_ENDPOINT
              value: "ldaps://testmyldap.com:636"
            - name: LDAP_MANAGER_DN_USERNAME
              value: "CN=john-service-user,OU=Administrators,DC=TESTMYLDAP,DC=COM"
            - name: LDAP_SERVER_DOMAIN
              value: "TESTMYLDAP"
            - name: LDAP_SEARCH_BASE
              value: "DC=TESTMYLDAP,DC=COM"
            - name: LDAP_SEARCH_FILTER
              value: "(sAMAccountName={username})"
            - name: LDAP_MANAGER_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: another-ldap-auth
                  key: LDAP_MANAGER_PASSWORD
```

Another LDAP Auth secret manifest, `another-secret.yaml`.
```
---
apiVersion: v1
kind: Secret
metadata:
  name: another-ldap-auth
  namespace: ingress-nginx
type: Opaque
data:
  LDAP_MANAGER_PASSWORD: <your-password-in-base64>
```

Another LDAP Auth service manifest, `another-service.yaml`.
```
---
kind: Service
apiVersion: v1
metadata:
  name: another-ldap-auth
  namespace: ingress-nginx
spec:
  type: ClusterIP
  selector:
    app: another-ldap-auth
  ports:
    - name: another-ldap-auth
      port: 80
      protocol: TCP
      targetPort: 9000
```

Ingress manifest for the application you want to add authentication. You can remove the un-comment and send headers as variables such as `Required groups`.
```
---
apiVersion: extensions/v1beta1
kind: Ingress
metadata:
  name: demo-webserver
  namespace: demo
  annotations:
    nginx.ingress.kubernetes.io/auth-url: http://another-ldap-auth.ingress-nginx.svc.cluster.local
    # nginx.ingress.kubernetes.io/auth-snippet: |
    #   proxy_set_header Ldap-Required-Groups "<SOME GROUP>";
    #   proxy_set_header Ldap-Required-Groups-Conditional "or";
spec:
  rules:
  - host: demo.local
    http:
      paths:
      - path: /
        backend:
          serviceName: demo-webserver
          servicePort: 80
```

## Available configurations parameters
The parameters can be sent via environment variables or via HTTP headers, also you can combine them.

The parameter `LDAP_SEARCH_FILTER` support variable expansion with the username, you can do something like this `(sAMAccountName={username})` and `{username}` is going to be replaced by the username typed in the login form.

### Environment variables
- `LDAP_ENDPOINT` LDAP URL with the port number. Ex: `ldaps://testmyldap.com:636`
- `LDAP_MANAGER_DN_USERNAME` Username to bind and search in the LDAP tree. Ex: `CN=john-service-user,OU=Administrators,DC=TESTMYLDAP,DC=COM`
- `LDAP_MANAGER_PASSWORD` Password for the bind user.
- `LDAP_SEARCH_BASE` Ex: `DC=TESTMYLDAP,DC=COM`
- `LDAP_SEARCH_FILTER` Filter to search, for Microsoft Active Directory usually you can use `sAMAccountName`. Ex: `(sAMAccountName={username})`
- `LDAP_SERVER_DOMAIN` **(Optional)**, for Microsoft Active Directory usually need the domain name for authenticate the user. Ex: `TESTMYLDAP.COM`
- `LDAP_REQUIRED_GROUPS` **(Optional)**, required groups are case insensitive (`DevOps` is the same as `DEVOPS`), you can send a list separated by commas, try first without required groups. Ex: `'DevOps', 'DevOps_QA'`
- `LDAP_REQUIRED_GROUPS_CONDITIONAL` **(Optional, default=and)**, you can set the conditional to match all the groups on the list or just one of them. To match all of them use `and` and for match just one use `or`. Ex: `and`
- `CACHE_EXPIRATION` **(Optional, default=5)** Expiration time in minutes for the cache. Ex: `10`

### HTTP headers
- `Ldap-Endpoint`
- `Ldap-Manager-Dn-Username`
- `Ldap-Manager-Password`
- `Ldap-Search-Base`
- `Ldap-Search-Filter`
- `Ldap-Server-Domain` **(Optional)**
- `Ldap-Required-Groups` **(Optional)**
- `Ldap-Required-Groups-Conditional` **(Optional)**

## Known limitations
- Parameters via headers need to be escaped, for example, you can not send parameters such as `$1` or `$test` because Nginx is applying variable expansion.
