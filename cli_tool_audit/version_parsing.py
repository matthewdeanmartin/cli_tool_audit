import re
from typing import Optional

import packaging.specifiers as ps
import packaging.version
import semver
from semver import Version


def extract_first_two_part_version(input_string):
    # Regular expression for 2 part version
    semver_regex = r"\d+\.\d+"

    # Find all matches in the string
    matches = re.findall(semver_regex, input_string)

    # Return the first match or None if no match is found
    return matches[0] if matches else None


def extract_first_semver_version(input_string):
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
