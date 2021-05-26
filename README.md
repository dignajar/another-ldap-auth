# Another LDAP authentication

**LDAP Authentication** for **Nginx**, **Kubernetes ingress controller** (Nginx), **HAProxy** ([haproxy-auth-request](https://github.com/TimWolla/haproxy-auth-request)) or any webserver/reverse proxy with authorization based on the result of a subrequest.

**Another LDAP Authentication** is an implementation of the `ldap-auth-daemon` services described in the official blog from Nginx in the [following article](https://www.nginx.com/blog/nginx-plus-authenticate-users/).

**Another LDAP Authentication** it's prepared to run inside a Docker container, also you can run the Python script without the Docker container.

[![Docker Hub](https://img.shields.io/badge/Docker-Hub-blue.svg)](https://hub.docker.com/r/dignajar/another-ldap-auth)

[![Kubernetes YAML manifests](https://img.shields.io/badge/Kubernetes-Deployment-blue.svg)](https://github.com/dignajar/another-ldap-auth/tree/master/kubernetes)

## Features
- Supports `ldap` and `ldaps`.
- Provide a cache for users, you can limit the time of the cache.
- Supports validation groups.
- Supports validation groups with conditionals and regex.
- Supports configuration via headers or via environment variables.
- Supports HTTP response headers such as username and matched groups.
- Log format in Plain-Text or JSON.

## Diagram
![Another LDAP Authentication](https://i.ibb.co/crJ0Xr2/diagram-1.png)

## Available configurations parameters
The parameters can be sent via environment variables or via HTTP headers, also you can combine them.

The parameter `LDAP_SEARCH_FILTER` support variable expansion with the username, you can do something like this `(sAMAccountName={username})` and `{username}` is going to be replaced by the username typed in the login form.

All values type are `string`.

### Environment variables
| Key                                 | Default   | Values                           | Description                                                                            | Example                                                        |
| ----------------------------------- | --------- | ---------------------------------| ---------------------------------------------------------------------------------------| ---------------------------------------------------------------|
| LDAP_ENDPOINT                       |           |                                  | LDAP URL with the protocol and the port number.                                        | `ldaps://testmyldap.com:636`                                   |
| LDAP_MANAGER_DN_USERNAME            |           |                                  | Username to bind and search in the LDAP tree.                                          | `CN=john,OU=Administrators,DC=TESTMYLDAP,DC=COM`               |
| LDAP_MANAGER_PASSWORD               |           |                                  | Password for the bind user.                                                            |                                                                |
| LDAP_SEARCH_BASE                    |           |                                  |                                                                                        | `DC=TESTMYLDAP,DC=COM`                                         |
| LDAP_SEARCH_FILTER                  |           |                                  | Filter for search, for Microsoft Active Directory usually you can use `sAMAccountName`.| `(sAMAccountName={username})`                                  |
| LDAP_SERVER_DOMAIN **(Optional)**   |           |                                  | Microsoft Active Directory usually need the domain name for authenticate the user.     | `TESTMYLDAP.COM`                                               |
| LDAP_MATCHING_USERS **(Optional)** |            |                                  | Support a list separated by commas.| `'diego,john,s-master'` |
| LDAP_MATCHING_GROUPS **(Optional)** |           |                                  | Supports regular expressions, and support a list separated by commas.| `'DevOps production environment', 'Developers .* environment'` |
| LDAP_MATCHING_GROUPS_CONDITIONAL    | `and`     | `and`, `or`                      | Conditional to match all the groups in the list or just one of them.                   | `or`                                                           |
| LDAP_MATCHING_GROUPS_CASE_SENSITIVE | `enabled` | `enabled`, `disabled`            | Enabled or disabled case sensitive groups matches.                                     | `disabled`                                                     |
| CACHE_EXPIRATION                    | `5`       |                                  | Cache expiration time in minutes.                                                      | `10`                                                           |
| LOG_LEVEL                           | `INFO`    | `INFO`, `WARNING`, `ERROR`       | Logger level.                                                                          | `DEBUG`                                                        |
| LOG_FORMAT                          | `TEXT`    | `TEXT`, `JSON`                   | Output format of the logger.                                                           | `JSON`                                                         |
| LDAP_HTTPS_SUPPORT                  | `disabled`| `enabled`, `disabled`            | Enabled or disabled HTTPS support with self signed certificate.                        |                                                                |

### HTTP request headers
The variables send via HTTP headers take precedence over environment variables.

- `Ldap-Endpoint`
- `Ldap-Manager-Dn-Username`
- `Ldap-Manager-Password`
- `Ldap-Search-Base`
- `Ldap-Search-Filter`
- `Ldap-Server-Domain`
- `Ldap-Matching-Users`
- `Ldap-Matching-Groups`
- `Ldap-Matching-Groups-Case-Sensitive`
- `Ldap-Matching-Groups-Conditional`

### HTTP response headers
- `x-username` Contains the authenticated username
- `x-groups` Contains the username matches groups

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
    -e LOG_FORMAT='JSON' \
    -p 9000:9000 \
    --name another_ldap_auth \
    dignajar/another-ldap-auth:latest
```

**Another LDAP Authentication** now is running on `http://localhost:9000`.

Test it via curl:
```
curl -vvv http://localhost:9000 -u diego:mypassword
```

Output from ALDAP:
```
{"date": "2021-05-21 10:06:52", "level": "INFO", "objectName": "Cache", "ip": "192.168.0.10", "referrer": null, "message": "User not found in the cache.", "username": "diego"}
{"date": "2021-05-21 10:06:52", "level": "INFO", "objectName": "Aldap", "ip": "192.168.0.10", "referrer": null, "message": "Authenticating user.", "username": "diego", "finalUsername": "diego"}
{"date": "2021-05-21 10:06:53", "level": "INFO", "objectName": "Aldap", "ip": "192.168.0.10", "referrer": null, "message": "Authentication successful.", "username": "diego", "elapsedTime": "0.22335"}
{"date": "2021-05-21 10:06:53", "level": "INFO", "objectName": "Cache", "ip": "192.168.0.10", "referrer": null, "message": "Adding user to the cache.", "username": "diego"}
192.168.0.10 - - [21/May/2021 10:06:53] "GET / HTTP/1.1" 200 -
```

> Remember you can enable self-signed certificate from Flask via the environment variable `LDAP_HTTPS_SUPPORT=="enabled"`.

### Step 2 - Nginx configuration
Nginx use the module [ngx_http_auth_request_module](http://nginx.org/en/docs/http/ngx_http_auth_request_module.html) to do the subrequest.

The following example shows how to configure Nginx that is running in the same machine as **Another LDAP Authentication**. The backend `/private/` includes the authentication request to `/another_ldap_auth`.

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

Now you can access to your website wich is going to be something like this `http://myserver.com/private/` and Nginx will request you to write the username and password.

## Deploy to Kubernetes with Nginx ingress controller
Get the K8s manifests from the folder `/kubernetes`.

The manifests for K8s helps to deploy **Another LDAP Authentication** in the namespace `ingress-nginx` and expose the service in the cluster at the following address `https://another-ldap-auth.ingress-nginx`.

Please change the environment variables from the manifest and the secret for the bind username.

After you have running **Another LDAP Authentication** in your Kubernetes, you can modify the ingress manifest from the application you want to protect.

You can remove the comment `#` and send headers as variables such as `Matching groups`.

```
---
apiVersion: extensions/v1beta1
kind: Ingress
metadata:
  name: demo-webserver
  namespace: demo
  annotations:
    nginx.ingress.kubernetes.io/auth-url: https://another-ldap-auth.ingress-nginx

    # nginx.ingress.kubernetes.io/auth-snippet: |
    #   proxy_set_header Ldap-Matching-Groups "<SOME GROUP>";
    #   proxy_set_header Ldap-Matching-Groups-Conditional "or";
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

## Known limitations
- Parameters via headers need to be escaped, for example, you can not send parameters such as `$1` or `$test` because Nginx is applying variable expansion.