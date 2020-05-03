from setuptools import setup

setup(
   name='MalBeacon Command-Line Client',
   version='1.0',
   description='A command-line client to interact with the MalBeacon API',
   author='Lars Wallenborn',
   author_email='lars@wallenborn.net',
   packages=['malbeacon-api'],
   install_requires=['requests', 'terminaltables'],
)
