import setuptools


with open("README.md", "r") as fh:
    long_description = fh.read()


setuptools.setup(
    name="newstagger",
    version="0.0.1",
    author="scrimmage",
    author_email="and.capuano@gmail.com",
    description="Package to update Scrimmage newsfeed's tags",
    long_description=long_description,
    url="https://github.com/Scrimmage-co/NewsTagger",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)