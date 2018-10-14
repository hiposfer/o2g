from setuptools import setup, find_packages

from osmtogtfs import __version__


def readme():
    with open('README.md') as f:
        return f.read()


setup(name='osmtogtfs',
      version=__version__,
      description='Extracts partial GTFS feed from OSM data.',
      long_description=readme(),
      long_description_content_type='text/markdown',
      author='Mehdi Sadeghi',
      author_email='mehdi@mehdix.org',
      url='https://github.com/hiposfer/osmtogtfs',
      keywords=['osm', 'gtfs'],
      license='MIT',
      platforms='any',
      packages=find_packages(),
      package_data={'': ['*.txt']},
      entry_points={
        'console_scripts': ['osmtogtfs=osmtogtfs.cli:cli',
                            'o2g=osmtogtfs.cli:cli']
      },
      zip_safe=False,
      test_suite='pytest',
      install_requires=['osmium'],
      classifiers=['Development Status :: 4 - Beta',
                   'Environment :: Console',
                   'Intended Audience :: End Users/Desktop',
                   'License :: OSI Approved :: MIT License',
                   'Natural Language :: English',
                   'Programming Language :: Python :: 3.4',
                   'Programming Language :: Python :: 3.5',
                   'Programming Language :: Python :: 3.6'])
