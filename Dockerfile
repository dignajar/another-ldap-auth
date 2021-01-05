FROM python:3.7.9-alpine3.12

ENV LDAP_ENDPOINT=""
ENV LDAP_MANAGER_DN_USERNAME=""
ENV LDAP_MANAGER_PASSWORD=""
ENV LDAP_SERVER_DOMAIN=""
ENV LDAP_SEARCH_BASE=""
ENV LDAP_SEARCH_FILTER=""
ENV LDAP_REQUIRED_GROUPS=""
ENV LDAP_REQUIRED_GROUPS_CONDITIONAL="and"
ENV LDAP_REQUIRED_GROUPS_CASE_SENSITIVE="enabled"
ENV LDAP_HTTPS_SUPPORT="disabled"

ENV PYTHONUNBUFFERED=0

RUN apk --no-cache add build-base openldap-dev libffi-dev
RUN pip install --no-cache-dir flask Flask-HTTPAuth python-ldap pyopenssl
COPY files/* /opt/

EXPOSE 9000
CMD ["python3", "-u", "/opt/main.py"]