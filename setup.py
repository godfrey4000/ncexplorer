"""First attempt at setup.py"""

from setuptools import setup, find_packages


setup (
	name='ncexplorer',
	version='0.0.1.dev3',
	description='Climate data analysis utility.',
	long_description='Climate data analysis utility.',
	url='https://github.com/godfrey4000/ncexplorer',
	license='MIT',
	classifiers=[
		'Development Status :: 3 - Alpha',
		'Intended Audience :: Science/Research',
		'Topic :: Scientific/Engineering :: Atmospheric Science',
		'License :: OSI Approved :: MIT License',
		'Programming Language :: Python :: 2.7',
	],
	keywords='climate netcdf analysis',

	# The packages
	packages=find_packages(exclude=['docs', 'etc', 'ncexplorer/test']),
#	install_requires=['xarray', 'esgf-pyclient'],
)

