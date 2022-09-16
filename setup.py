from os import path

from setuptools import find_packages, setup

PROJECT_ROOT = path.abspath(path.dirname(__file__))

with open(path.join(PROJECT_ROOT, "README.md"), encoding="utf-8") as f:
    LONG_DESCRIPTION = f.read()

requires_base = ["rengu >= 6.0", "requests", "beautifulsoup4"]
requires_extra = {}

requires_extra["all"] = [m for v in requires_extra.values() for m in v]

setup(
    name="rengu-webgrab",
    version="6.0",
    description="Rengu I Ching Functions",
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    url="https://rengu.io",
    author="Thornton K. Prime",
    author_email="thornton.prime@gmail.com",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.8",
    ],
    packages=find_packages(),
    install_requires=requires_base,
    extras_require=requires_extra,
    entry_points={
        "rengu_template": [
            "webgrab_reading = rengu_template_webgrab:RenguTemplateWebgrab"
        ]
    },
)
