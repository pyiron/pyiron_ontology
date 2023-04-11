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

    classifiers=['Development Status :: 3 - Alpha',
                 'Topic :: Scientific/Engineering :: Physics',
                 'License :: OSI Approved :: BSD License',
                 'Intended Audience :: Science/Research',
                 'Operating System :: OS Independent',
                 'Programming Language :: Python :: 3.8',
                 'Programming Language :: Python :: 3.9',
                 'Programming Language :: Python :: 3.10'],

    keywords='pyiron',
    packages=find_packages(exclude=["*tests*", "*docs*", "*binder*", "*conda*", "*notebooks*", "*.ci_support*"]),
    install_requires=[
        'numpy',
        'owlready2',
        'pandas',
        'pint',
        'pyiron_atomistics>=0.2.63',
        'sqlalchemy',
    ],
    cmdclass=versioneer.get_cmdclass(),

    )
