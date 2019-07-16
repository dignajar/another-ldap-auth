# Another LDAP authentication

**LDAP Authentication** for **Nginx**, **Kubernetes ingress controller** (Nginx), **HAProxy** ([haproxy-auth-request](https://github.com/TimWolla/haproxy-auth-request)) or any webserver/reverse proxy with authorization based on the result of a subrequest.

**Another LDAP Authentication** is an implementation of the `ldap-auth-daemon` services described in the official blog from Nginx in the [following article](https://www.nginx.com/blog/nginx-plus-authenticate-users/).

**Another LDAP Authentication** it's prepared to run inside a Docker container, also you can run the Python script without the Docker container.

**Another LDAP Authentication** supports `ldap` and `ldaps`.

## Diagram
![Nginx-LDAP-Auth-Daemon](https://www.nginx.com/wp-content/uploads/2016/02/ldap-auth-components.jpg)

## Installation and configuration
The easy way to use **Another LDAP Authentication** is running as a Docker container.

Run as a Docker container
```
docker run -d \
        -e LDAP_ENDPOINT='ldaps://testmyldap.com:636' \
        -e LDAP_MANAGER_DN_USERNAME='CN=john-service-user,OU=Administrators,DC=TESTMYLDAP,DC=COM' \
        -e LDAP_MANAGER_PASSWORD='MasterpasswordNotHack123' \
        -e LDAP_SERVER_DOMAIN='TESTMYLDAP.COM' \
        -e LDAP_SEARCH_BASE='DC=TESTMYLDAP,DC=COM' \
        -e LDAP_SEARCH_FILTER='(sAMAccountName={username})' \
        -e LDAP_REQUIRED_GROUPS='"DevOps", "DevOps_QA"' \
        -p 9000:9000 \
        --name another_ldap_auth \
        docker.hub.com/another_ldap_auth:0.1
```

### Nginx configuration
Nginx use the module [ngx_http_auth_request_module](http://nginx.org/en/docs/http/ngx_http_auth_request_module.html) to do the subrequest.

The following example shows how to configure Nginx which is running in the same machine as **Another LDAP Authentication** on the port `9000`.

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

## Available configurations parameters
The parameters can be sent via environment variables or via HTTP headers, also you can combine them.

### Environment variables
- `LDAP_ENDPOINT` LDAP URL with the port number. Ex: `ldaps://testmyldap.com:636`
- `LDAP_MANAGER_DN_USERNAME` Username to bind and search in the LDAP tree. Ex: `CN=john-service-user,OU=Administrators,DC=TESTMYLDAP,DC=COM`
- `LDAP_MANAGER_PASSWORD` Password for the bind user.
- `LDAP_SEARCH_BASE` Ex: `DC=TESTMYLDAP,DC=COM`
- `LDAP_SEARCH_FILTER` Filter to search, for Microsoft Active Directory usually you can use `sAMAccountName`. Ex: `(sAMAccountName={username})`
- `LDAP_SERVER_DOMAIN` (Optional), for Microsoft Active Directory usually need the domain name for authenticate the user. Ex: `TESTMYLDAP.COM`
- `LDAP_REQUIRED_GROUPS` (Optional), required groups are case insensitive (`DevOps` is the same as `DEVOPS`), you can send a list separated by commas, try first without required groups. Ex: `'DevOps', 'DevOps_QA'`

### HTTP headers
- `Ldap-Endpoint`
- `Ldap-Manager-Dn-Username`
- `Ldap-Manager-Password`
- `Ldap-Search-Base`
- `Ldap-Search-Filter`
- `Ldap-Server-Domain` (Optional)
- `Ldap-Required-Groups` (Optional)

## Known limitations
- Parameters via headers need to be escaped, for example, you can not send parameters such as `$1` or `$test` because Nginx is applying variable expansion.