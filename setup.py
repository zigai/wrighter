from setuptools import setup, find_packages
with open('./requirements.txt') as f:
    requirements = f.read().splitlines()

setup(name="scraper-base",
      version="0.0.1",
      description="Base class for quickly building web scrapers using playwright.",
      author="Žiga Ivanšek",
      packages=find_packages(),
      install_requires=requirements)
