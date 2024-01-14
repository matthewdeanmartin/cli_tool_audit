from semver import Version

from cli_tool_audit.version_parsing import extract_first_semver_version, two_pass_semver_parse


def test_multi_line():
    example = """pyreverse is included in pylint:
pylint 3.0.3
astroid 3.0.2
Python 3.11.1 (tags/v3.11.1:a7a450f, Dec  6 2022, 19:58:39) [MSC v.1934 64 bit (AMD64)]"""
    assert extract_first_semver_version(example) == "3.0.3"
    example = r"""
                 _                 _
                (_) ___  ___  _ __| |_
                | |/ _/ / _ \/ '__  _/
                | |\__ \/\_\/| |  | |_
                |_|\___/\___/\_/   \_/

      isort your imports, so you don't have to.

                    VERSION 5.13.2"""
    assert extract_first_semver_version(example) == "5.13.2"


def test_simple_extraction():
    # Test the function with your examples
    example1 = "shiv, version 1.0.3"
    example2 = "shiv, version 1.0.3 (deps foo 2.0.1, bar 3.0.1, plugins 5.0.1)"

    assert extract_first_semver_version(example1) == "1.0.3"
    assert extract_first_semver_version(example2) == "1.0.3"


def test_other_cases():
    example1 = "SyntaxError"
    example2 = "1.2"

    assert extract_first_semver_version(example1) is None
    assert extract_first_semver_version(example2) is None


def test_two_part():
    print(two_pass_semver_parse("2.10") == Version(2, 10, 0))
    print(two_pass_semver_parse("llm, version 0.12") == Version(0, 12, 0))


def test_two_pass():
    result = two_pass_semver_parse("vulture 2.10")
    assert result == Version(2, 10, 0)
