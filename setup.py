import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="saturno",
    version="1.8.0",
    author="Moris Doratiotto",
    author_email="moris.doratiotto@gmail.com",
    description="A python module to download anime from Anime Saturn",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mortafix/Saturno",
    packages=setuptools.find_packages(),
    install_requires=[
        "requests",
        "bs4",
        "halo",
        "pymortafix",
        "halo",
        "argparse",
        "python-telegram-bot",
        "youtube-dl",
    ],
    classifiers=[
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
    ],
    python_requires=">=3.8",
    keywords=["anime", "saturn", "download"],
    package_data={"saturno": ["anime.py", "getchar.py", "manage.py", "config.json"]},
    entry_points={"console_scripts": ["saturno=saturno.saturno:main"]},
)
