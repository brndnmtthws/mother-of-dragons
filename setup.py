import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="mother-of-dragons",
    version="0.1.5",
    author="Brenden Matthews",
    author_email="brenden@diddyinc.com",
    description="Python-based management tool for DragonMint T1",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/brndnmtthws/mother-of-dragons",
    packages=setuptools.find_packages(),
    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ),
    entry_points={
        'console_scripts':
            ['mother-of-dragons=mother_of_dragons.main:main'],
    },
)
