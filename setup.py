import pathlib

from setuptools import find_packages, setup

HERE = pathlib.Path(__file__).parent
README = (HERE / "README.md").read_text()
REQUIREMENTS = (HERE / "requirements.txt").read_text()

setup(
    name="wrighter",
    version="0.3.4",
    description="",
    long_description=README,
    long_description_content_type="text/markdown",
    author="Ziga Ivansek",
    author_email="ziga.ivansek@gmail.com",
    url="https://github.com/zigai/wrighter",
    license="MIT",
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3 :: Only",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    packages=find_packages(),
    package_dir={'wrighter': 'wrighter'},
    install_requires=REQUIREMENTS,
)
