#!/usr/bin/env python3
"""Fetch only application secrets using the VM's managed identity; print no values."""
import json
import os
from pathlib import Path
import urllib.parse
import urllib.request

os.umask(0o077)
token_url='http://169.254.169.254/metadata/identity/oauth2/token?api-version=2018-02-01&resource='+urllib.parse.quote('https://vault.azure.net',safe='')
request=urllib.request.Request(token_url,headers={'Metadata':'true'})
token=json.load(urllib.request.urlopen(request,timeout=20))['access_token']
def secret(name):
    request=urllib.request.Request('https://dmiw07kv20260926.vault.azure.net/secrets/'+name+'?api-version=7.4',headers={'Authorization':'Bearer '+token})
    return json.load(urllib.request.urlopen(request,timeout=20))['value']
values=dict(DB_NAME='bookreview',DB_USER='bookapp',DB_PASS=secret('db-password'),DB_HOST='dmi-w07-20260926-mysql.mysql.database.azure.com',DB_PORT='3306',JWT_SECRET=secret('jwt-secret'),PORT='5000',NODE_ENV='production')
for v in values.values():
    if any(c in v for c in '\n\r"\\'):raise ValueError('Unsupported environment value')
Path('/etc/week07-book.env').write_text(''.join(k+'="'+v+'"\n' for k,v in values.items()))
Path('/etc/week07-book.env').chmod(0o600)
print('Managed identity fetched two Key Vault secrets; root-only environment file ready. Values withheld.')
