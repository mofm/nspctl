from setuptools import setup
import nspctl


classifiers = [
    "Development Status :: 4 - Beta",
    "Environment :: Console",
    "Intended Audience :: Developers",
    "Intended Audience :: Information Technology",
    "Intended Audience :: System Administrators"
    "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
    "Operating System :: POSIX :: Linux",
    "Programming Language :: Python",
    "Programming Language :: Python :: 3.8",
    "Topic :: System :: Systems Administration",
    "Topic :: Terminals",
    "Topic :: Utilities"
]


setup(
    name='nspctl',
    version=nspctl.__version__,
    packages=['nspctl', 'nspctl.utils'],
    url='https://github.com/mofm/nspctl',
    license='GPLv3',
    author='Emre Eryilmaz',
    author_email='emre.eryilmaz@piesso.com',
    description='nspctl, management tool for systemd-nspawn containers',
    scripts=['scripts/nspctl'],
    classifiers=classifiers,
    keywords='nspawn, container, systemd, systemd-nspawn, systemd-container',
    python_requires='>=3.8',

)
