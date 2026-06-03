#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ridna_library.settings')
    if len(sys.argv) > 1 and sys.argv[1] == 'makemessages':
        ignored_paths = ('venv/*', '.venv/*', 'env/*', '.env/*')
        existing_ignores = {
            sys.argv[index + 1]
            for index, argument in enumerate(sys.argv[:-1])
            if argument == '--ignore'
        }
        for pattern in ignored_paths:
            if pattern not in existing_ignores:
                sys.argv.extend(['--ignore', pattern])
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
