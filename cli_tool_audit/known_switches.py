"""
This file contains a dictionary of known switches for various CLI tools.
"""
KNOWN_SWITCHES = {
    "npm": "version",
    "terraform": "-version",  # modern versions also support --version
    "java": "-version",  # modern versions also support --version
}
