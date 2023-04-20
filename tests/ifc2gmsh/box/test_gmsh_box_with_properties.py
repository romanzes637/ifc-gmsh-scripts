from ifc2gmsh.main import main


def test_fenia_box_with_properties(box_props_path='box_with_properties.ifc',
                                   output_dir_path='gmsh_props'):
    main(box_props_path, output_dir_path)
