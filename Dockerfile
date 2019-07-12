FROM python:alpine3.10

ENV LDAP_ENDPOINT=""
ENV LDAP_MANAGER_DN_USERNAME=""
ENV LDAP_MANAGER_PASSWORD=""
ENV LDAP_SERVER_DOMAIN=""
ENV LDAP_SEARCH_BASE=""
ENV LDAP_SEARCH_FILTER=""
ENV LDAP_REQUIRED_GROUPS=""

ENV PYTHONUNBUFFERED=0

RUN apk --no-cache add build-base openldap-dev python3-dev
RUN pip install --no-cache-dir flask Flask-HTTPAuth python-ldap
COPY files/* /opt/

EXPOSE 9000
CMD ["python3", "-u", "/opt/main.py"]