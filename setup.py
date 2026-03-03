from setuptools import setup, find_packages

setup(
    name='hal-azure-access',
    version='1.0.0',
    description='HAL for Azure Access Technology BLU-IC2',
    author='CST Physical Access Control',
    packages=find_packages(),
    python_requires='>=3.6',
    install_requires=[
        'pyyaml',
    ],
    entry_points={
        'console_scripts': [
            'hal-provision=python.card_provisioning:main',
            'hal-monitor=python.event_monitor:main',
        ],
    },
)
