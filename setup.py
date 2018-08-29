from setuptools import setup
from os import path

classifiers = [
  'Development Status :: 4 - Beta',
  'Intended Audience :: Financial and Insurance Industry',
  'Programming Language :: Python',
  'Operating System :: OS Independent',
  'Natural Language :: English',
  'License :: OSI Approved :: BSD License'
]

# read the contents of your README file
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(name='pacli',
      version='0.4.5',
      description='Simple CLI PeerAssets client.',
      long_description=long_description,
      long_description_content_type='text/markdown',
      keywords=['peerassets', 'blockchain', 'assets', 'client'],
      url='https://github.com/peerassets/pacli',
      author='Peerchemist',
      author_email='peerchemist@protonmail.ch',
      license='GPL',
      packages=['pacli'],
      install_requires=['pypeerassets', 'terminaltables',
                        'appdirs', 'fire', 'keyring',
                        ],
      entry_points={
          'console_scripts': [
              'pacli = pacli.__main__:main'
          ]}
      )
