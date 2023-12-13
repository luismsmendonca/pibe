from distutils.core import setup

VERSION = "0.14"

testing_extras = [
    "pytest",
    "coverage",
    "pytest-cov",
]

setup(
    name="pibe",
    py_modules=['pibe'],
    packages=['pibe_ext'],
    version=VERSION,
    license="MIT",
    description="pibe is a webob router.",
    author="Luis Mendonca",
    author_email="luismsmendonca@gmail.com",
    url="https://github.com/luismsmendonca/pibe",
    download_url=f"https://github.com/luismsmendonca/pibe/archive/refs/tags/v{VERSION}.tar.gz",
    keywords=["webob", "router"],
    install_requires=[
        "webob",
    ],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
    ],
    extras_require={"testing": testing_extras},
)
