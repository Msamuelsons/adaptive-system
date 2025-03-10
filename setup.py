from setuptools import setup, find_packages

setup(
    name='adaptive-system',
    version='0.0.1',
    description='Adaptive system project using machine learning concepts',
    long_description=open("docs/README.md").read(),
    long_description_content_type="text/markdown",
    author="Msamuelsons",
    packages=find_packages(),
    install_requires=[
        'pygame',
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires=">=3.6",
)
