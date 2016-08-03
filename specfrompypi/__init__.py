__author__ = 'jmartinez'
__version__ = '1.0.0'

import os
import click
import requests
import requirements
import shutil
import subprocess
import sys
import tarfile
import tempfile
import zipfile

from datetime import date
from glob import glob as ls
from jinja2 import Environment, FileSystemLoader
from uuid import uuid4

from pkg_resources import RequirementParseError

def find_dependencies(directory):
    cwd = os.getcwd()
    os.chdir(directory)
    dependencies = set()
    single_version_externally_managed = True
    _requirements = ['{}/requirements.txt'.format(directory)]
    try:
        subprocess.check_output([sys.executable, 'setup.py', 'egg_info'])
        _requirements.extend(ls('{}/*.egg-info/requires.txt'.format(directory)))
    except subprocess.CalledProcessError:
        click.echo('egg_info not supported by {}'.format(directory))
        single_version_externally_managed = False

    try:
        for _requirement in _requirements:
            if not os.path.isfile(_requirement):
                continue

            click.echo('Reading requirements file {}'.format(_requirement))
            with open(_requirement, 'r') as f:
                try:
                    for req in requirements.parse(f):
                        if req.specs:
                            dependencies.add('{} {}'.format(req.name,
                                ''.join([ '{} {}'.format(o, v)
                                          for o,v in req.specs])))
                        else:
                            dependencies.add(req.name)
                except RequirementParseError:
                    pass

    finally:
        os.chdir(cwd)
        shutil.rmtree(directory)
        return dependencies, single_version_externally_managed


def extract_files(_file):
    def extract_tar(_file, tmpdir):
        tar = tarfile.open(_file)
        os.makedirs(tmpdir)
        os.chdir(tmpdir)
        tar.extractall()

    def extract_zip(_file, tmpdir):
        with zipfile.ZipFile(_file) as _zip:
            os.makedirs(tmpdir)
            os.chdir(tmpdir)
            _zip.extractall()

    name, extension = os.path.splitext(_file)
    if extension == '.gz':
        _, _extension = os.path.splitext(name)
        extension = '{}{}'.format(_extension, extension)
        name = name.replace(_extension, '')

    tmpdir = "{}/{}".format(tempfile.gettempdir(), uuid4())
    cwd = os.getcwd()

    if extension in ['.tar.gz', '.tgz', '.tar.bz2']:
        extract_tar(_file, tmpdir)
    elif extension == '.zip':
        extract_zip(_file, tmpdir)

    os.chdir(cwd)
    return os.path.join(tmpdir, name)


def create(meta):
    os.mkdir(meta['package_name'])
    click.echo('Downloading {}'.format(meta['source']))
    cwd = os.getcwd()
    os.chdir(meta['package_name'])
    _file = download_file(meta['source'])
    click.echo('Extracting {}'.format(_file))
    extracted = extract_files(_file)
    click.echo('Searching for extra dependencies on {}'.format(extracted))
    extra_deps, single_version_externally_managed = find_dependencies(extracted)
    if not single_version_externally_managed:
        meta.update({'single_version_externally_managed': False})

    meta['requires'].extend(extra_deps)
    os.chdir(cwd)

    env = Environment(loader=FileSystemLoader('{}/templates'.format(
            os.path.dirname(os.path.abspath(__file__)))))
    spec = env.get_template('python-spec.tmpl')
    rendered = spec.render(meta)
    with open('{name}/{name}.spec'.format(
            name=meta['package_name']), 'w') as spec:
        spec.write(rendered)


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
    click.echo('Building metadata for the package genaration...')
    meta = {'name': pypi['info']['name']}
    meta.update({'source':
        next((url['url'] for url in pypi['urls']
            if 'source' in url['python_version']
            and ('tar.gz' in url['url'] or
                 'zip' in url['url'] or
                 'tar.bz2' in url['url'])), '')
    })
    if meta['source'] == '':
        click.echo("Cannot determine download URL... "
              "Check Pypi: https://pypi.python.org/pypi/{}/"
              .format(meta['name']))
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
    meta.update({'single_version_externally_managed': True})
    return meta


def read_pypi(name, version=None):
    click.echo('Trying to fetch pypi information about {}...'.format(name))
    if not version:
        url = "https://pypi.python.org/pypi/{}/json".format(name)
    else:
        url = "https://pypi.python.org/pypi/{}/{}/json".format(name, version)
    result = requests.get(url)
    if result.status_code == 200:
        pypi = result.json()
    else:
        click.echo("Package or release not found on {}".format(url))
        sys.exit(2)

    return build_metadata(pypi)


def run(name, python_prefix, recursive):
    meta = read_pypi(name)
    package_name = '{}-{}'.format(python_prefix, meta['name'])
    if os.path.isdir(package_name):
        click.echo('{} already exists, skipping...'.format(package_name))
        return
    meta.update({'python_prefix': python_prefix})
    meta.update({'package_name': package_name})
    create(meta)
    if recursive:
        for dep in meta['requires']:
            ## Todo:
            # Refactor here to actually enfore the version
            dep = dep.replace('>', ' ').replace('<', ' ').\
                    replace('=', '/').split()[0]
            run(dep, python_prefix, recursive)


@click.command()
@click.argument('name')
@click.option('--python_prefix', '-p', default='python35')
@click.option('--recursive', '-r', is_flag=True)
def cli(name, python_prefix, recursive):
    if os.path.isdir(name):
        click.echo("Package {} alreayd exists".format(name))
        sys.exit(1)

    run(name, python_prefix, recursive)
    sys.exit(0)

if __name__ == '__main__':
    cli()
