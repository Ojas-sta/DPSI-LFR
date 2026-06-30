from setuptools import setup, find_packages

setup(
    name='dpsi-lfr',
    version='1.0.0',
    py_modules=['hardware', 'cli', 'vision', 'main', 'control', 'feedback'],
    install_requires=[
        'pyserial',
        'gpiozero',
        'opencv-python',
        'numpy',
        'mpu6050-raspberrypi',
        'smbus2'
    ],
    entry_points={
        'console_scripts': [
            'lfr-cli=cli:main',
        ],
    },
)
