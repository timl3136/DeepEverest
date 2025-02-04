from setuptools import setup, Extension
from sys import platform

# Compile *deepeverst_index.cpp* into a shared library
print(platform)

if platform == "linux" or platform == "linux2":
    # linux
    setup(
        # ...
        ext_modules=[
            Extension('deepeverst_index',
                      sources=['deepeverst_index.cpp'],
                      extra_compile_args=['-std=c++14'],
                      extra_link_args=[])]
    )
elif platform == "darwin":
    # OSX
    setup(
        # ...
        ext_modules=[
            Extension('deepeverst_index',
                      sources=['deepeverst_index.cpp'],
                      extra_compile_args=['-std=c++14', '-mmacosx-version-min=10.9'],
                      extra_link_args=['-stdlib=libc++', '-mmacosx-version-min=10.9'])]
    )
