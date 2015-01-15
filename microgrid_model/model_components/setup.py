from distutils.core import setup
from Cython.Build import cythonize

setup(
  ext_modules = cythonize("power_network_helper_functions.pyx"),
)