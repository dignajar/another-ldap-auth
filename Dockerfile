FROM python:3.9.5-alpine3.13

ENV LDAP_ENDPOINT=""
ENV LDAP_MANAGER_DN_USERNAME=""
ENV LDAP_MANAGER_PASSWORD=""
ENV LDAP_SEARCH_BASE=""
ENV LDAP_SEARCH_FILTER=""
ENV FLASK_SECRET_KEY="CHANGE_ME!"

ENV PYTHONUNBUFFERED=0
ENV CRYPTOGRAPHY_DONT_BUILD_RUST=1

RUN apk --no-cache add build-base openldap-dev libffi-dev
COPY files/requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt --no-cache-dir

ENV USER aldap
ENV HOME /home/$USER
RUN adduser -D $USER
USER $USER
WORKDIR $HOME

COPY files/* $HOME

EXPOSE 9000
CMD ["python3", "-u", "main.py"]