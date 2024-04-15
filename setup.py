"""
Setuptools based setup module
"""
from setuptools import setup, find_packages
import versioneer

setup(
    name='pyiron_ontology',
    version=versioneer.get_version(),
    description='pyiron_ontology - module extension to pyiron.',
    long_description='http://pyiron.org',

    url='https://github.com/pyiron/pyiron_ontology',
    author='Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department',
    author_email='liamhuber@greyhavensolutions.com',
    license='BSD',

    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Topic :: Scientific/Engineering :: Physics',
        'License :: OSI Approved :: BSD License',
        'Intended Audience :: Science/Research',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],

    keywords='pyiron',
    packages=find_packages(exclude=["*tests*", "*docs*", "*binder*", "*conda*", "*notebooks*", "*.ci_support*"]),
    install_requires=[
        'numpy==1.26.3',
        'owlready2==0.46',
        'pandas==2.2.2',
        'pint==0.23',
    ],
    extras_require={
        "pyiron_atomistics": [],
    },
    cmdclass=versioneer.get_cmdclass(),

    )
