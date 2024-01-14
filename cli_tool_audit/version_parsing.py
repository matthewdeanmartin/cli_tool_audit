import re
from typing import Optional

import packaging.specifiers as ps
import packaging.version
import semver
from semver import Version


def extract_first_two_part_version(input_string: str) -> Optional[str]:
    """
    Extract the first 2 part version from a string.
    Args:
        input_string (str): The string to parse.

    Returns:
        Optional[str]: The first 2 part version if found, None otherwise.

    Examples:
        >>> extract_first_two_part_version("1.2.3")
        '1.2'
        >>> extract_first_two_part_version("1.2")
        '1.2'
        >>> extract_first_two_part_version("1") is None
        True
        >>> extract_first_two_part_version("1.2.3a1")
        '1.2'
        >>> extract_first_two_part_version("1.2.3a1.post1")
        '1.2'
    """
    # Regular expression for 2 part version
    semver_regex = r"\d+\.\d+"

    # Find all matches in the string
    matches = re.findall(semver_regex, input_string)

    # Return the first match or None if no match is found
    return matches[0] if matches else None


def extract_first_semver_version(input_string: str) -> Optional[str]:
    """
    Extract the first semver version from a string.
    Args:
        input_string (str): The string to parse.

    Returns:
        Optional[str]: The first semver version if found, None otherwise.

    Examples:
        >>> extract_first_semver_version("1.2.3")
        '1.2.3'
        >>> extract_first_semver_version("1.2") is None
        True
        >>> extract_first_semver_version("1.2.3a1")
        '1.2.3'
        >>> extract_first_semver_version("1.2.3a1.post1")
        '1.2.3'

    """
    # Regular expression for semver version
    semver_regex = r"\d+\.\d+\.\d+"

    # Find all matches in the string
    matches = re.findall(semver_regex, input_string)

    # Return the first match or None if no match is found
    return matches[0] if matches else None


# packaging.version.Version
def convert2semver(ver: packaging.version.Version) -> semver.Version:
    """Converts a PyPI version into a semver version

    :param ver: the PyPI version
    :return: a semver version
    :raises ValueError: if epoch or post parts are used
    """
    if ver.epoch:
        raise ValueError("Can't convert an epoch to semver")
    if ver.post:
        raise ValueError("Can't convert a post part to semver")

    pre = None if not ver.pre else "".join([str(i) for i in ver.pre])

    if len(ver.release) == 3:
        major, minor, patch = ver.release
        return semver.Version(major, minor, patch, prerelease=pre, build=ver.dev)
    major, minor = ver.release
    return semver.Version(major, minor, prerelease=pre, build=ver.dev)


def two_pass_semver_parse(input_string: str) -> Optional[Version]:
    """
    Parse a string into a semver version. This function will attempt to parse the string twice.
    The first pass will attempt to parse the string as a semver version. If that fails, the second pass will attempt to
    parse the string as a PyPI version. If that fails, the third pass will attempt to parse the string as a 2 part
    version. If that fails, the fourth pass will attempt to parse the string as a 1 part version. If that fails, None
    is returned.

    Args:
        input_string (str): The string to parse.

    Returns:
        Optional[Version]: A semver version if the string can be parsed, None otherwise.

    Examples:
        >>> two_pass_semver_parse("1.2.3")
        Version(major=1, minor=2, patch=3, prerelease=None, build=None)
        >>> two_pass_semver_parse("1.2")
        Version(major=1, minor=2, patch=0, prerelease=None, build=None)
        >>> two_pass_semver_parse("1.2.3a1")
        Version(major=1, minor=2, patch=3, prerelease='a1', build=None)
        >>> two_pass_semver_parse("1.2.3a1.post1")
        Version(major=1, minor=2, patch=3, prerelease=None, build=None)
    """
    # empty never works
    if not input_string:
        return None

    # Clean semver string
    try:
        possible = Version.parse(input_string)
        return possible
    except ValueError:
        pass
    except TypeError:
        pass

    # Clean pypi version, including 2 part versions

    # pylint: disable=broad-exception-caught
    try:
        pypi_version = ps.Version(input_string)
        possible = convert2semver(pypi_version)
        if possible:
            return possible
    except BaseException:
        pass

    possible_first = extract_first_semver_version(input_string)
    if possible_first:
        try:
            possible = Version.parse(possible_first)
            return possible
        except ValueError:
            pass
        except TypeError:
            pass

    possible_first = extract_first_two_part_version(input_string)
    if possible_first:
        try:
            pypi_version = ps.Version(possible_first)
            possible = convert2semver(pypi_version)
            return possible
        except ValueError:
            pass
        except TypeError:
            pass
    # Give up. This doesn't appear to be semver
    return None


if __name__ == "__main__":
    convert2semver(packaging.version.Version("1.2"))

    convert2semver(packaging.version.Version("1.2.3"))
