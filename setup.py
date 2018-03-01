from setuptools import setup

def readme():
    with open('README.md') as f:
        return f.read()

setup(name='osmtogtfs',
      version='0.1.7',
      description='Extracts partial GTFS feed from OSM data.',
      long_description=readme(),
      author='Mehdi Sadeghi',
      author_email='mehdi@mehdix.org',
      url='https://github.com/hiposfer/osmtogtfs',
      keywords=['osm', 'gtfs'],
      license='MIT',
      platforms='any',
      packages=['osmtogtfs'],
      entry_points={
        'console_scripts': ['osmtogtfs=osmtogtfs.cli:cli']
      },
      include_package_data=True,
      zip_safe=False,
      test_suite='pytest',
      install_requires=['osmium', 'timezonefinder', 'click', 'setuptools'],
      classifiers=['Development Status :: 4 - Beta',
                   'Environment :: Console',
                   'Intended Audience :: End Users/Desktop',
                   'License :: OSI Approved :: MIT License',
                   'Natural Language :: English',
                   'Programming Language :: Python :: 3.4',
                   'Programming Language :: Python :: 3.5',
                   'Programming Language :: Python :: 3.6']
     )
