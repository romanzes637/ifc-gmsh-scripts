import json
from pathlib import Path
import argparse

import ifcopenshell

import ifc2fenia.foam as foam


def ifc2py(v):
    try:
        return v.wrappedValue
    except AttributeError:
        return v


def main(file_path, output_dir_path='gmsh'):
    # Read
    file_path = Path(file_path)
    ifc = ifcopenshell.open(str(file_path))
    products = ifc.by_type('IfcProduct')
    print(f'products: {len(products)}')

    # Read/Write
    output_dir_path = Path(output_dir_path)
    output_dir_path.mkdir(parents=True, exist_ok=True)
    for product in products:
        gid = ifc2py(product.GlobalId)
        if gid == '2wGebYoZr8CujW8_P1W8tC':
            for x in product.IsDefinedBy:
                if hasattr(x, 'RelatingPropertyDefinition'):
                    if x.RelatingPropertyDefinition.is_a('IfcPropertySet'):
                        prop_set = x.RelatingPropertyDefinition
                        prop_set_name = ifc2py(prop_set.Name)
                        if prop_set_name == 'IBRAE_Gmsh':
                            gmsh_data = {'data': {"class": "block.Block"}}
                            volumes_zones = None
                            surfaces_zones = None
                            for y in prop_set.HasProperties:
                                prop_name = ifc2py(y.Name)
                                if prop_name == 'VolumeZones':
                                    volumes_zones = [ifc2py(x) for x in ifc2py(y.ListValues)]
                                elif prop_name == 'SurfacesZones':
                                    surfaces_zones = [ifc2py(x) for x in ifc2py(y.ListValues)]
                                elif prop_name == 'BooleanLevel':
                                    gmsh_data['data']['boolean_level'] = ifc2py(y.NominalValue)
                            if volumes_zones is not None and surfaces_zones is not None:
                                gmsh_data['data']['zone'] = [volumes_zones[0], surfaces_zones]
                            elif volumes_zones is not None:
                                gmsh_data['data']['zone'] = volumes_zones[0]
                            else:
                                raise ValueError('Volume zone should be defined!')
                            data_path = output_dir_path / gid
                            print(gid)
                            print(gmsh_data)
                            with open(data_path, 'w') as f:
                                json.dump(gmsh_data, f)
