from setuptools import setup, find_packages
with open('./requirements.txt') as f:
    requirements = f.read().splitlines()

setup(name="wrighter",
      version="0.0.2",
      description="Quickly build web scrapers with Playwright. ",
      author="Ziga Ivansek",
      packages=find_packages(),
      install_requires=requirements)
