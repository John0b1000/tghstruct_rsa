from setuptools import setup, find_packages

setup(
    name='tgdhstruct',
    version='1.1.2',
    packages=find_packages(),
    url='https://github.com/John0b1000/tgdhstruct',
    license='GNU General Public License v3.0',
    author='John Nori',
    author_email='johnlnori8@gmail.com',
    description='Tree Structure for TGDH Implementation',
    install_requires=[
        'anytree',
        'pycryptodome',
        'osbrain',
    ]
)
