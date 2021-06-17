from setuptools import find_packages
from setuptools import setup


setup(
    name='robinhood',
    packages=find_packages(exclude=(['test*', 'tmp*', 'pyrh'])),
    version='0.1',
    license='GNU GPL v3',
    install_requires=[
        'pyotp',
        'sqlalchemy',
    ],
)
