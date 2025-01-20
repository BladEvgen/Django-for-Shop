import os

def create_directories():
    script_directory = os.path.dirname(os.path.abspath(__file__))
    parent_directory = os.path.dirname(script_directory)

    directories = ["log", "database"]

    for directory in directories:
        path = os.path.join(parent_directory, directory)
        os.makedirs(path, exist_ok=True)
        print(f"Created directory: {path}")


if __name__ == "__main__":
    create_directories()
