from setuptools import setup, find_packages

setup(
    name='nlplab',
    version='1.0.0',
    packages=find_packages(exclude=['docs', 'tests*']),
    python_requires='>=3',
    url='http://galadriel02.korea.ncsoft.corp/searchtf/pypi/nlplab',
    license='MIT',
    author='ejpark',
    author_email='ejpark@ncsoft.com',
    description='nlplab 데이터셋 배포 라이브러리'
)
