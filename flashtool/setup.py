from setuptools import setup, find_packages

setup(
    name='flashtool',
    version='0.5.1',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Click',
    ],
    extras_require={
        'dev': ['pytest', 'pypandoc'],
    },
    entry_points='''
        [console_scripts]
        flashtool=flashtool.cli:cli
    ''',
)
