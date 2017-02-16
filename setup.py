from setuptools import setup

setup(name='pacli',
      version='0.2',
      description='Simple CLI PeerAssets client.',
      url='https://github.com/peerassets/pacli',
      author='Peerchemist',
      author_email='peerchemist@protonmail.ch',
      license='GPL',
      packages=['pacli'],
      install_requires=['pypeerassets', 'terminaltables'],
      entry_points={
          'console_scripts': [
              'pacli = pacli.__main__:main'
          ]}
     )
