import os
import subprocess


def run_migrations():
    script_directory = os.path.dirname(os.path.abspath(__file__))
    parent_directory = os.path.dirname(script_directory)

    operating_system = os.name

    os.chdir(parent_directory)

    if operating_system == "posix":
        activate_script = os.path.join(parent_directory, "env", "bin", "activate")
        activate_command = f"source {activate_script}"
    elif operating_system == "nt":
        activate_script = os.path.join(parent_directory, "env", "Scripts", "activate")
        activate_command = f"call {activate_script}"
    else:
        print("Unsupported operating system")
        return

    migrate_command = "python manage.py makemigrations && python manage.py migrate"

    try:
        subprocess.run(
            f"{activate_command} && {migrate_command}", shell=True, check=True
        )
    except subprocess.CalledProcessError as e:
        print(f"Error running migrations: {e}")


if __name__ == "__main__":
    run_migrations()
