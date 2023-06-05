from setuptools import setup, find_packages

setup(
    name='devopsapi_module',
    version='0.0.1',
    install_requires=[
        'redis'
    ],
    packages=find_packages()
)