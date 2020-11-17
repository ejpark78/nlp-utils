from setuptools import setup, find_packages

setup(
    name='crawler',
    version='1.0.0',
    packages=find_packages(exclude=['docs', 'tests*']),
    python_requires='>=3',
    url='',
    license='Apache License Version 2.0',
    author='ejpark',
    author_email='ejpark@ncsoft.com',
    description='크롤러'
)
