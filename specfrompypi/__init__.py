__author__ = 'jmartinez'
__version__ = '1.0.0'

import os
import requests
import sys

from datetime import date
from jinja2 import Environment, FileSystemLoader


def create(meta):
    env = Environment(loader=FileSystemLoader('{}/templates'.format(
            os.path.dirname(os.path.abspath(__file__)))))
    spec = env.get_template('python-spec.tmpl')
    rendered = spec.render(meta)
    os.mkdir(meta['name'])
    with open('{name}/{name}.spec'.format(name=meta['name']), 'w') as spec_file:
        spec_file.write(rendered)
    os.chdir(meta['name'])
    download_file(meta['source'])


def download_file(url):
    local_filename = url.split('/')[-1]
    r = requests.get(url, stream=True)
    with open(local_filename, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)
                f.flush()
    return local_filename


def build_metadata(pypi):
    meta = {'name': pypi['info']['name']}
    meta.update({'source':
        next((url['url'] for url in pypi['urls']
            if 'source' in url['python_version']
            and ('tar.gz' in url['url'] or
                 'zip' in url['url'] or
                 'tar.bz2' in url['url'])), '')
    })
    if meta['source'] == '':
        print("Cannot determine download URL... "
              "Check Pypi: https://pypi.python.org/pypi/{}/".format(meta['name']))
        sys.exit(3)

    meta.update(
        {'version': (meta['source'].split('-')[-1].
                     replace('.tar.gz', '').
                     replace('.zip', '').
                     replace('.tar.bz2', ''))}
    )
    meta.update({'url': pypi['info']['home_page']})
    meta.update({'summary': pypi['info']['summary']})
    meta.update({'license': pypi['info']['license']})
    meta.update({'requires': pypi['info'].get('requires', [])})
    meta.update({'author': pypi['info']['author']})
    meta.update({'description': pypi['info'].get(
        'description', meta['summary'])}
    )
    meta.update({'me': os.getenv('PACKAGER_NAME')})
    meta.update({'email': os.getenv('PACKAGER_EMAIL')})
    meta.update({'date': date.today().strftime("%a %b %d %Y")})
    return meta


def read_pypi(name, version=None):
    if not version:
        url = "https://pypi.python.org/pypi/{}/json".format(name)
    else:
        url = "https://pypi.python.org/pypi/{}/{}/json".format(name, version)
    result = requests.get(url)
    if result.status_code == 200:
        pypi = result.json()
    else:
        print("Package or release not found on {}".format(url))
        sys.exit(2)

    return build_metadata(pypi)


def main():
    name = sys.argv[1]
    if os.path.isdir(name):
        print("Package {} alreayd exists".format(name))
        sys.exit(1)

    meta = read_pypi(name)
    create(meta)
    sys.exit(0)
