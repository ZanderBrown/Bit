from setuptools import setup
from bit import __version__


setup(
    name='Bit',
    version=__version__,
    description='Python Editor for Micro::Bit',
    author='Alexander Brown',
    url='https://github.com/ZanderBrown/Bit',
    packages=['bit'],
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        'Environment :: X11 Applications :: Gtk',
        'Intended Audience :: Education',
        'Topic :: Education',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3',
    ],
    entry_points={
        'console_scripts': [
            "bit = bit.app:run",
        ],
    },
    data_files=[('/etc/udev/rules.d', ['conf/90-usb-microbit.rules', ]),
                ('/usr/share/applications', ['conf/bit.desktop', ])],
)
