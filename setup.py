from setuptools import setup, find_packages
import os

setup(
   name='weasel-make',
   version='0.3.1',
   packages=find_packages(),
   install_requires=[],
   entry_points={
       'console_scripts': [
           'weasel=weasel_make.weasel:main',
       ],
   },
   # Metadata
   author='Mirror12k',
   description='A Makefile-compatibile Build Tool',
   long_description=open('README.md').read(),
   long_description_content_type='text/markdown',
   license='MIT',
   keywords='make build-tool weasel makefile',
   url='https://github.com/mirror12k/weasel-make',
   include_package_data=True,
   classifiers=[
       'Programming Language :: Python :: 3',
       'License :: OSI Approved :: MIT License',
   ],
)
