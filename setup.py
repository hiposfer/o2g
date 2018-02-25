from setuptools import setup

def readme():
    with open('README.md') as f:
        return f.read()

setup(name='osmtogtfs',
      version='0.1.6',
      description='Extracts partial GTFS feed from OSM data.',
      long_description=readme(),
      author='Mehdi Sadeghi',
      author_email='mehdi@mehdix.org',
      url='https://github.com/hiposfer/osmtogtfs',
      packages=['_osmtogtfs'],
      py_modules=['osmtogtfs'],
      entry_points='''
        [console_scripts]
        osmtogtfs=osmtogtfs:cli
      ''',
      license='MIT',
      platforms='any',
      install_requires=['osmium', 'timezonefinder', 'click', 'setuptools'],
      keywords=['osm', 'gtfs'],
      classifiers=['Development Status :: 4 - Beta',
                   'Environment :: Console',
                   'Intended Audience :: End Users/Desktop',
                   'License :: OSI Approved :: MIT License',
                   'Natural Language :: English',
                   'Programming Language :: Python :: 3.4',
                   'Programming Language :: Python :: 3.5',
                   'Programming Language :: Python :: 3.6']
     )
