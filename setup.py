import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

requires = [
    'gevent>=1.3.7',
    'requests>=2.20.1',
    'statsd>=3.2.2',
    'dragon-rest>=0.2.3',
    'serpy>=0.3.1',
    'toml>=0.10.0',
]
test_requires = [
    'pytest-cov',
    'vcrpy>=1.12.0',
    'pytest>=3.6.1',
    'pytest-mock>=1.10.0'
]

setuptools.setup(
    name="mother-of-dragons",
    version="0.2.8",
    author="Brenden Matthews",
    author_email="brenden@diddyinc.com",
    description="Python-based management tool for DragonMint and Innosilicon miners",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/brndnmtthws/mother-of-dragons",
    packages=setuptools.find_packages(),
    include_package_data=True,
    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ),
    entry_points={
        'console_scripts':
            ['mother-of-dragons=mother_of_dragons.main:main'],
    },
    python_requires=">=3.5",
    install_requires=requires,
    tests_require=test_requires,
    extras_require={
        'test': test_requires,
    },
)
