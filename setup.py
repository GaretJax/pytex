import os
import platform

from setuptools import setup, find_packages


class Setup(object):
    @staticmethod
    def read(fname, fail_silently=False):
        """
        Utility function to read the content of the given file.
        """
        try:
            return open(os.path.join(os.path.dirname(__file__), fname)).read()
        except:
            if not fail_silently:
                raise
            return ''


    @staticmethod
    def requirements(fname):
        """
        Utility function to create a list of requirements from the output of the
        pip freeze command saved in a text file.
        """
        packages = Setup.read(fname).split('\n')
        packages = (p.strip() for p in packages)
        packages = (p for p in packages if p and not p.startswith('#'))
        return list(packages)


    @staticmethod
    def get_files(*bases):
        """
        Utility function to list all files in a data directory.
        """
        for base in bases:
            basedir, _ = base.split('.', 1)
            base = os.path.join(os.path.dirname(__file__), *base.split('.'))

            rem = len(os.path.dirname(base))  + len(basedir) + 2

            for root, dirs, files in os.walk(base):
                for name in files:
                    yield os.path.join(basedir, root, name)[rem:]


if platform.system() == 'Darwin':
    fs_monitor = 'macfsevents'
elif platform.system() == 'Linux':
    fs_monitor = 'pyinotify'
else:
    raise Exception("Only works on OS X and Linux")


setup(
    name='pytex',
    version='0.1a',
    description='Command line utility to ease working on LaTeX documents.',
    author='Jonathan Stoppani',
    author_email='jonathan@stoppani.name',
    url='https://github.com/garetjax/pytex',
    download_url='https://github.com/garetjax/pytex/tarball/0.1a',
    license='MIT',
    packages=find_packages(),
    package_dir = {'pytex': 'pytex'},
    package_data = {
        'pytex': ['default-settings.ini'],#list(Setup.get_files('pytex.pytex')),
    },
    install_requires=Setup.requirements('requirements.txt') + [fs_monitor],
    entry_points=Setup.read('entry-points.ini', True),
)
