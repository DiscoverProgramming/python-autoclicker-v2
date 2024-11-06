from setuptools import setup, find_packages

setup(
    name="python-autoclicker-v2",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "PyQt6",
        "pyautogui"
    ],
    entry_points={
        "console_scripts": [
            "autoclicker=main:main",
        ],
    },
    description="A simple auto clicker application using PyQt6 and pyautogui.",
    python_requires='>=3.6',
)
