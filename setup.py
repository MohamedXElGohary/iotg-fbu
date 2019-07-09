import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="elkhart-lake-platmform-firmware-and-bios-utilities",
    version="0.2.0",
    author="Intel Corp.",
    author_email="build.admin@intel.com",
    description="Stitching, signing and capsule creation scripts",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://gitlab.devtools.intel.com/OWR/IoTG/BDP/Bootloader/PMT/siip_tools.git",
    packages=setuptools.find_packages(exclude=["*.tests"]),
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'SIIPSign=siipSign.SIIPSign:main',
            'SIIPStitch=siipStitch.SIIPStitch:main',
            'GenerateSubRegionCapsule=SubRegionCapsule.GenerateSubRegionCapsule:main',
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
    ],
)