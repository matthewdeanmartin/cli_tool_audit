import os
import re
from typing import Any

import toml


def read_poetry_metadata() -> Any:
    # Path to the pyproject.toml file
    pyproject_path = "pyproject.toml"

    # Read the pyproject.toml file
    with open(pyproject_path) as file:
        data = toml.load(file)

    # Extract the [tool.poetry] section
    poetry_data = data.get("tool", {}).get("poetry", {})
    return poetry_data


def write_metadata_to_file(poetry_data: dict[str, Any]) -> None:
    # Extract the project name and create a directory
    project_name = poetry_data.get("name")
    dir_path = f"./{project_name}"
    os.makedirs(dir_path, exist_ok=True)

    # Define the path for the __about__.py file
    about_file_path = os.path.join(dir_path, "__about__.py")

    # https://web.archive.org/web/20111010053227/http://jaynes.colorado.edu/PythonGuidelines.html#module_formatting
    meta = [
        "name",  # title
        "version",
        "description",
        "authors",  # credits/ author/ author_email
        "license",  # copyright
        "homepage",  # url
        "keywords",
    ]

    # Missing
    # - maintainer (same as author/credits?)
    # __maintainer_email__
    # - copyright (same as license?) = (C) Author Date
    # - summary (same as description?)
    # __docformat__ = "restructuredtext" or "restructuredtext en"
    # uri - same as url?
    # - contact (same as author_email, maintiner, etc)
    # - __date__
    # __doc__
    # __author__ and __keywords__ are sometimes lists sometimes space delim strings
    # __longdescr__
    # __classifiers__  - list of trove classifiers
    # __package__
    # release_date
    # __project_url__ = 'https://github.com/spyder-ide/spyder'
    # __forum_url__   = 'https://groups.google.com/group/spyderlib'
    # __trouble_url__ = __project_url__ + '/wiki/Troubleshooting-Guide-and-FAQ'

    content = []
    for key, value in poetry_data.items():
        if key == "name":
            # __name__ is a reserved name.
            content.append(f'__title__ = "{value}"')
            continue
        if key == "authors" and isinstance(value, list):
            if len(value) == 1:
                scalar = value[0].strip("[]' ")
                email_pattern = "<([^>]+@[^>]+)>"
                match = re.search(email_pattern, scalar)
                if match is not None:
                    email = match.groups()[0]
                    author = scalar.replace("<" + email + ">", "").strip()
                    content.append(f'__author__ = "{author}"')
                    content.append(f'__author_email__ = "{email}"')
                else:
                    content.append(f'__author__ = "{scalar}"')

            else:
                content.append(f'__credits__ = "{value}"')
        elif key == "classifiers" and isinstance(value, list):
            for trove in value:
                if trove.startswith("Development Status"):
                    content.append(f'__status__ = "{trove.split("::")[1].strip()}"')
        elif key == "keywords" and isinstance(value, list):
            content.append(f"__keywords__ = {value}")
        elif key in meta:
            content.append(f'__{key}__ = "{value}"')
        else:
            print(f"Skipping: {key}")

    all_header = "__all__ = [\n" + ",\n".join([f'    "{item.split("=")[0].strip()}"' for item in content]) + "\n]"
    # Define the content to write to the __about__.py file
    about_content = "\n".join(content)

    docstring = f"""\"\"\"Metadata for {project_name}.\n\"\"\"\n\n"""
    # Write the content to the __about__.py file
    with open(about_file_path, "w") as file:
        file.write(docstring)
        file.write(all_header)
        file.write("\n\n")
        file.write(about_content)

    print(f"Metadata written to {about_file_path}")


def main():
    poetry_data = read_poetry_metadata()
    if poetry_data:
        write_metadata_to_file(poetry_data)
    else:
        print("No [tool.poetry] section found in pyproject.toml.")


if __name__ == "__main__":
    main()
