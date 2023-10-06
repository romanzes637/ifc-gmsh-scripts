import argparse


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--file_path')
    parser.add_argument('--output_dir_path')
    parser.add_argument('-t', '--type', default='geometry')
    args = parser.parse_args()
    kwargs = vars(args)
    t = kwargs.pop('type', None)
    if t == 'geometry':
        from ifc2gmsh.geometry import main
        main(**kwargs)
    elif t == 'properties':
        from ifc2gmsh.properties import main
        main(**kwargs)
    else:
        raise NotImplementedError(t)
