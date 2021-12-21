FROM python:3.9.9-alpine3.14

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

# Run as non-root
ENV USER aldap
ENV UID 10001
ENV GROUP aldap
ENV GID 10001
ENV HOME /home/$USER
RUN addgroup -g $GID -S $GROUP && adduser -u $UID -S $USER -G $GROUP

# Python code
COPY files/* $HOME/
RUN chown -R $USER:$GROUP $HOME

EXPOSE 9000
USER $UID:$GID
WORKDIR $HOME
CMD ["python3", "-u", "main.py"]
