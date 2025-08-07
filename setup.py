from setuptools import setup, find_packages
from typing import List

def get_requirements() ->List[str]:
    """Reads requirements from requirements.txt file"""

    requirements_list = []
    try:
        with open('requirements.txt', "r") as file:
            lines = file.readlines()
            for line in lines:
                requirement = line.strip()
                if requirement and requirement != "-e .":
                    requirements_list.append(requirement)
    except FileNotFoundError:
        print("requirements.txt not found")

    return requirements_list

setup (
    name='Radiology_report',

    version='0.1',
    author='Irshad',
    author_email='irshadmm16@gmail.com',
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=get_requirements(),
)