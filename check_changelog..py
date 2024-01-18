import keepachangelog

if __name__ == "__main__":
    changes = keepachangelog.to_dict("CHANGELOG.md")
    print(changes)
    content = keepachangelog.from_dict(changes)
    # so far only whitespace differences?
    with open("CHANGELOG_2.md", "w") as file:
        file.write(content)
    print(content)
