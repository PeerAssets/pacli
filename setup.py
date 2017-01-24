from setuptools import setup

setup(name='pacli',
      version='0.1',
      description='Simple CLI PeerAssets client.',
      url='https://github.com/peerassets/pacli',
      author='Peerchemist',
      author_email='peerchemist@protonmail.ch',
      license='GPL',
      packages=['pacli'],
      install_requires=['pypeerassets', 'terminaltables'],
      zip_safe=True)
