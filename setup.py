from setuptools import setup, find_packages

with open('requirements.txt', 'r') as fp:
    install_requires = [x.strip() for x in fp.readlines()]

setup(
    name='nlplab',
    version='1.0.0',
    packages=find_packages(exclude=['docs', 'tests*']),
    python_requires='>=3',
    url='http://galadriel02.korea.ncsoft.corp/searchtf/pypi/nlplab',
    license='Apache License Version 2.0',
    author='ejpark',
    author_email='ejpark@ncsoft.com',
    description='nlplab 데이터셋 배포 라이브러리',
    install_requires=install_requires
)
