import argparse
import os

from .database import make_engine, migrate


def main():
    parser = argparse.ArgumentParser(description='Fridgely database release commands')
    parser.add_argument('command', choices=['migrate'])
    parser.parse_args()
    engine = make_engine(os.getenv('DATABASE_URL', 'sqlite:///./fridgely.db'))
    try:
        migrate(engine)
    finally:
        engine.dispose()


if __name__ == '__main__':
    main()
