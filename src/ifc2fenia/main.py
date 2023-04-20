from pathlib import Path
import argparse

import ifcopenshell

import ifc2fenia.foam as foam


def ifc2py(v):
    try:
        return v.wrappedValue
    except AttributeError:
        return v


def main(file_path, output_dir_path='fenia'):
    # Read
    file_path = Path(file_path)
    ifc = ifcopenshell.open(str(file_path))
    property_sets = ifc.by_type('IfcPropertySet')
    print(f'property_sets: {len(property_sets)}')

    # Get data
    initial_conditions = {}
    boundary_conditions = {}
    material_properties = {}
    for x in property_sets:
        prop_set_name = ifc2py(x.Name)
        if prop_set_name == 'IBRAE_Fenia':
            for y in x.HasProperties:
                name = ifc2py(y.Name)
                if name in ['BoundaryCondition', 'InitialCondition', 'MaterialProperty']:
                    uname = ifc2py(y.UsageName)
                    if name == 'BoundaryCondition':
                        boundary_conditions.setdefault(uname, []).append(y)
                    elif name == 'InitialCondition':
                        initial_conditions.setdefault(uname, []).append(y)
                    elif name == 'MaterialProperty':
                        material_properties.setdefault(uname, []).append(y)
    print(initial_conditions)
    print(boundary_conditions)
    print(material_properties)

    # Write BC
    output_dir_path = Path(output_dir_path)
    output_dir_path.mkdir(parents=True, exist_ok=True)
    foam_bcs = {
        "FeniaFile": {
            "version": 2.0,
            "format": "ascii",
            "class": "dictionary",
            "location": "const",
            "object": "condition"}}
    for bc_name, bc_values in boundary_conditions.items():
        assert len(set(bc_values)) == 1
        bc = bc_values[0]
        foam_bc = {}
        for p in bc.HasProperties:
            key = ifc2py(p.Name)
            value = ifc2py(p.NominalValue)
            if key in ['timeValueTr']:
                key = f'{key} const'
            foam_bc[key] = value
        foam_bcs[bc_name] = foam_bc
    bcs_path = output_dir_path / 'constant' / 'T'
    bcs_path.parent.mkdir(parents=True, exist_ok=True)
    with open(bcs_path, 'w') as f:
        foam.dump(foam_bcs, f, cls='dictionary')

    # Write MAT and IC
    foam_mats = {
        "FeniaFile": {
            "version": 2.0,
            "format": "ascii",
            "class": "dictionary",
            "location": "const",
            "object": "transportProperties"},
        "noZone": {
            "matType": "constProp",
            "DT": [1.5, 1.5, 1.5],
            "rho": 2760.0,
            "cHeat": 800
        }
    }
    for mat_name, mat_values in material_properties.items():
        assert len(set(mat_values)) == 1
        foam_mat = {}
        mat = mat_values[0]
        for p in mat.HasProperties:
            key = ifc2py(p.Name)
            value = ifc2py(p.NominalValue)
            if key in ['Young', 'Poisson', 'alpha', 'stressCoeff', 'Hard']:
                key = f'{key} const'
            if key in ['DT'] and isinstance(value, (float, int)):
                value = [value, value, value]
            foam_mat[key] = value
        ics = initial_conditions.get(mat_name, None)
        if ics is not None:
            assert len(set(ics)) == 1
            ic = ics[0]
            for p in ic.HasProperties:
                key = ifc2py(p.Name)
                value = ifc2py(p.NominalValue)
                if key != 'type':
                    foam_mat[key] = value
        foam_mats[mat_name] = foam_mat
    mat_path = output_dir_path / 'constant' / 'termProperty'
    mat_path.parent.mkdir(parents=True, exist_ok=True)
    with open(mat_path, 'w') as f:
        foam.dump(foam_mats, f, cls='dictionary')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--file_path')
    parser.add_argument('--output_dir_path')
    args = parser.parse_args()
    kwargs = vars(args)
    main(**kwargs)
