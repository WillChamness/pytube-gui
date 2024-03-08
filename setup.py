from setuptools import find_packages, setup

with open("README.md", "r") as f:
    long_description = f.read()

setup(
    name="pytube_gui",
    version="0.1.2",
    license="GPLv3",
    description="A Qt application for the pytube library",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=["pytube>=15.0.0", "PyQt6>=6.0.0"],
    python_requires=">=3.8",
    entry_points={
        "gui_scripts": ["pytube-gui = pytube_gui:run"]
    },
)
