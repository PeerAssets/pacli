from setuptools import setup

setup(name='pacli',
      version='0.2.9',
      description='Simple CLI PeerAssets client.',
      keywords=['peerassets', 'blockchain', 'assets', 'client'],
      url='https://github.com/peerassets/pacli',
      author='Peerchemist',
      author_email='peerchemist@protonmail.ch',
      license='GPL',
      packages=['pacli'],
      install_requires=['pypeerassets', 'terminaltables', 'appdirs', 'click', 'click-default-group'],
      entry_points={
          'console_scripts': [
              'pacli = pacli.__main__:main'
          ]}
      )
