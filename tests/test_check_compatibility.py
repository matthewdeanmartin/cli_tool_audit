from cli_tool_audit import version_parsing
from cli_tool_audit.compatibility import check_compatibility, split_version_match_pattern


def test_any_will_do_compatible():
    assert check_compatibility("*", "2.0")[0] == "Compatible"


def test_not_compatible():
    assert check_compatibility(">1.0.0", "0.1.0") != "Compatible"


def test_compatible():
    assert check_compatibility(">1.0", "2.0")[0] == "Compatible"
    assert check_compatibility(">1.0.0", "2.0")[0] == "Compatible"
    assert check_compatibility(">=2.10", "2.10")[0] == "Compatible"

    assert check_compatibility(">=2.10", "2.10")[0] == "Compatible"
    assert check_compatibility(">=2.10", "vulture 2.10")[0] == "Compatible"


def test_multiline():
    example = """openjdk 17.0.6 2023-01-17
    OpenJDK Runtime Environment Temurin-17.0.6+10 (build 17.0.6+10)
    OpenJDK 64-Bit Server VM Temurin-17.0.6+10 (build 17.0.6+10, mixed mode, sharing)"""
    assert check_compatibility(">=17.0.6", example)[0] == "Compatible"


def test_ascii_art():
    example = r"""
                 _                 _
                (_) ___  ___  _ __| |_
                | |/ _/ / _ \/ '__  _/
                | |\__ \/\_\/| |  | |_
                |_|\___/\___/\_/   \_/

      isort your imports, so you don't have to.

                    VERSION 5.13.2"""
    assert check_compatibility(">=5.13.2", example)[0] == "Compatible"

    again = r"""
                 _                 _
                (_) ___  ___  _ __| |_
                | |/ _/ / _ \/ '__  _/
                | |\__ \/\_\/| |  | |_
                |_|\___/\___/\_/   \_/

      isort your imports, so you don't have to.

                    VERSION 5.13.2"""
    assert check_compatibility("==5.13.2", again)[0] == "Compatible"

    again_any = r"""_                 _
                   (_) ___  ___  _ __| |_
                   | |/ _/ / _ \/ '__  _/
                   | |\__ \/\_\/| |  | |_
                   |_|\___/\___/\_/   \_/

         isort your imports, so you don't have to.

                       VERSION 5.13.2"""
    assert check_compatibility("*", again_any)[0] == "Compatible"


def test_isort_semver():
    found_version = r"""_                 _
                       (_) ___  ___  _ __| |_
                       | |/ _/ / _ \/ '__  _/
                       | |\__ \/\_\/| |  | |_
                       |_|\___/\___/\_/   \_/

             isort your imports, so you don't have to.

                           VERSION 5.13.2"""
    symbols, desired_version_text = split_version_match_pattern(found_version)
    version_parsing.two_pass_semver_parse(desired_version_text)
    version_parsing.two_pass_semver_parse(found_version)
