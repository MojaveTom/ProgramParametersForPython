import setuptools
import wheel

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="progparams", # Replace with your own username
    version="0.0.1",
    author="Thomas DeMay",
    author_email="tom@demayfamily.com",
    description="Functions to create and initialize program parameters.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/MojaveTom/ProgramParametersForPython",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
    install_requires=[
        "commentjson",
        "toml",
        "schema",
    ],
)