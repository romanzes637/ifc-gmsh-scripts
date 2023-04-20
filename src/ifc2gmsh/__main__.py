import argparse
from ifc2gmsh.main import main


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--file_path')
    parser.add_argument('--output_dir_path')
    args = parser.parse_args()
    kwargs = vars(args)
    main(**kwargs)
