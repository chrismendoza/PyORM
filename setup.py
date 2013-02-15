import os
from setuptools import setup, find_packages

f = open(os.path.join(os.path.dirname(__file__), 'README.txt'))
readme = f.read()
f.close()

setup(
    name='PyORM',
    version='0.2.0',
    author='Chris Mendoza',
    author_email='chris.mendoza@pyorm.com',
    packages=['pyorm'],
    url='http://github.com/chrismendoza/PyORM/',
    license='LICENSE.txt',
    description='an ORM',
    long_description=readme,
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],
    test_suite='pyorm.test'
)
