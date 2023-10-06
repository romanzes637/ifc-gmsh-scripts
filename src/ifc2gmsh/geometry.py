from collections import Counter
import json
from pathlib import Path
from pprint import pprint
import shutil

import ifcopenshell
from ifcopenshell.util.placement import get_local_placement, get_axis2placement
import numpy as np
from tqdm import tqdm


def create_main_gmsh_object():
    gmsh_obj = {
        'metadata': {
            'run': {
                # 'factory': 'geo',
                # "strategy": {
                #     "class": "strategy.Base",
                #     "zone_function": {
                #         "class": "zone.Block",
                #         "dims": [3]}},
                'factory': 'occ',
                "options": {
                    "Mesh.Algorithm": 6,
                    "Mesh.Algorithm3D": 1,
                    "Mesh.MeshSizeFactor": 1,
                    "Mesh.MeshSizeMin": 0,
                    "Mesh.MeshSizeMax": 1e3,
                    "Mesh.MeshSizeFromPoints": 0,
                    "Mesh.MeshSizeFromParametricPoints": 0,
                    "Mesh.MeshSizeExtendFromBoundary": 0,
                    "Mesh.MeshSizeFromCurvature": 42,
                    "Mesh.MeshSizeFromCurvatureIsotropic": 0,
                    "Mesh.MinimumLineNodes": 2,
                    "Mesh.MinimumCircleNodes": 3,
                    "Mesh.MinimumCurveNodes": 3
                }
            }},
        'data': {'class': 'block.Block',
                 'do_register': False,
                 'children': [],
                 'children_transforms': []}}
    return gmsh_obj


def parse_ifc_faceted_brep(item, zone_name=None):
    zone_name = f'IfcFacetedBrep.{item.id()}' if zone_name is None else zone_name
    gmsh_obj = {'data': {'class': 'block.Polyhedron', 'zone': zone_name}}
    points_coordinates = {}
    points_old2new = {}
    polygons = []
    for f in item.Outer.CfsFaces:  # IfcFace
        polygon = []
        for b in f.Bounds:  # IfcFaceOuterBound, IfcFaceBound
            loop = []
            for point in b.Bound.Polygon:  # IfcPolyLoop
                new_id = points_old2new.setdefault(point.id(), len(points_old2new))
                loop.append(new_id)
                points_coordinates.setdefault(new_id, list(point.Coordinates))
            polygon.append(loop)
        if len(polygon) == 1:
            polygon = polygon[0]
        polygons.append(polygon)
    n_points = len(points_coordinates)
    gmsh_obj['data']['polygons'] = polygons
    gmsh_obj['data']['points'] = [points_coordinates[x] for x in range(n_points)]
    return gmsh_obj


def parse_extruded_area_solid(item):
    if item.SweptArea.is_a('IfcCircleHollowProfileDef'):
        direction = item.ExtrudedDirection.DirectionRatios
        assert direction == (0., 0., 1.)
        r1 = item.SweptArea.Radius - item.SweptArea.WallThickness
        r2 = item.SweptArea.Radius
        h = item.Depth
        # items_zone = [f"V{item_id}", f"V{item_id}"]
        items_zone = [f'IfcCircleHollowProfileDef.{item.id()}']
        gmsh_object = {
            "data": {
                "class": "block.Layer",
                "layer": [[r1, r2], [h]],
                "layer_curves": [["circle_arc", "circle_arc"], ["line"]],
                "items_zone": items_zone,
                "items_do_register_map": [0, 1],
                "items_boolean_level_map": 0}}
    elif item.SweptArea.is_a('IfcRectangleProfileDef'):
        direction = item.ExtrudedDirection.DirectionRatios
        assert direction == (0., 0., 1.)
        dx = item.SweptArea.XDim
        dy = item.SweptArea.YDim
        dz = item.Depth
        hx, hy = 0.5 * dx, 0.5 * dy
        points = [
            [hx, hy, 0], [-hx, hy, 0], [-hx, -hy, 0], [hx, -hy, 0],
            [hx, hy, dz], [-hx, hy, dz], [-hx, -hy, dz], [hx, -hy, dz],
        ]
        # zone = f"V{shape_id}"
        zone = f'IfcRectangleProfileDef.{item.id()}'
        gmsh_object = {
            "data": {
                "class": "block.Block",
                "zone": zone,
                "points": points,
                "boolean_level": 0}}
    elif item.SweptArea.is_a('IfcCircleProfileDef'):
        direction = item.ExtrudedDirection.DirectionRatios
        assert direction == (0., 0., 1.)
        r = item.SweptArea.Radius
        h = item.Depth
        items_zone = [f'items_zone.{item.id()}']
        gmsh_object = {
            "data": {
                "class": "block.Layer",
                "layer": [[r], [h]],
                "layer_curves": [["circle_arc"], ["line"]],
                "items_zone": items_zone,
                "items_boolean_level_map": 0}}
    else:
        raise NotImplementedError(item.SweptArea.get_info())
    return gmsh_object


def main(file_path, output_dir_path='gmsh'):
    ifc = ifcopenshell.open(file_path)
    gmsh_dir = output_dir_path
    owner_history = ifc.by_type("IfcOwnerHistory")[0]
    project = ifc.by_type("IfcProject")[0]
    context = ifc.by_type("IfcGeometricRepresentationContext")[0]
    print(ifc.by_type("IfcOwnerHistory"))

    products = ifc.by_type('IfcProduct')
    print(f'products: {len(products)}')
    pprint(Counter([x.is_a() for x in products]))
    shapes = ifc.by_type('IfcShapeRepresentation')
    print(f'shapes: {len(shapes)}')
    pprint(Counter([x.RepresentationIdentifier for x in shapes]))
    pprint(Counter([y.is_a() for x in shapes for y in x.Items]))
    structure = {}
    for i, shape in enumerate(shapes):
        structure.setdefault(shape.RepresentationType, []).append(shape)
    # pprint(structure)
    print('shapes structure:')
    pprint({k: len(v) for k, v in structure.items()})

    transformations = ifc.by_type('IfcGeometricRepresentationItem')
    print(f'transformations: {len(transformations)}')
    # pprint([(x.get_info(), ifc.get_inverse(x))
    #         for x in ifc.by_type('IfcAxis2Placement3D')
    #         if x.Location.Coordinates != (0, 0, 0)])
    pprint(Counter([x.is_a() for x in transformations]))

    gmsh_path = Path(gmsh_dir)
    if gmsh_path.exists():
        shutil.rmtree(gmsh_path)
    gmsh_path.mkdir(exist_ok=True, parents=True)
    main_obj = create_main_gmsh_object()
    id2file = {}
    allowed_items = {}
    # allowed_items = {52667, 52365, 52481}

    for shape in tqdm(structure.get('Brep', [])):
        for i, item in enumerate(shape.Items):  # IfcFacetedBrep
            item_id = item.id()
            if item_id not in allowed_items and len(allowed_items) != 0:
                continue
            gmsh_file = f'{item_id}.json'
            id2file[item_id] = gmsh_file
            gmsh_obj = parse_ifc_faceted_brep(item)
            with open(gmsh_path / gmsh_file, 'w') as f:
                json.dump(gmsh_obj, f)

    for shape in tqdm(structure.get('SweptSolid', [])):
        for item in shape.Items:
            item_id = item.id()
            if item_id not in allowed_items and len(allowed_items) != 0:
                continue
            gmsh_file = f'{item_id}.json'
            id2file[item_id] = gmsh_file
            if item.is_a('IfcExtrudedAreaSolid'):
                gmsh_obj = parse_extruded_area_solid
                with open(gmsh_path / gmsh_file, 'w') as f:
                    json.dump(gmsh_obj, f)
            else:
                raise NotImplementedError(item.get_info())

    for product in tqdm(products):
        placement = product.ObjectPlacement
        placement_matrix = get_local_placement(placement)
        product_representation = product.Representation
        if product_representation is not None:
            assert len(product_representation.Representations) == 1
            for r in product_representation.Representations:
                # if len(r.Items) != 1:
                #     print(f'{r.get_info()}: number of items {len(r.Items)} != 1')
                #     continue
                for i in r.Items:
                    try:
                        target = i.MappingTarget
                        source = i.MappingSource
                        source_representation = source.MappedRepresentation
                        for item in source_representation.Items:
                            item_id = item.id()
                            if item_id not in allowed_items and len(allowed_items) != 0:
                                continue
                            gmsh_file = id2file[item_id]
                            if source_representation.RepresentationType in ['SweptSolid']:
                                m = get_axis2placement(
                                    source.MappedRepresentation.Items[0].Position)
                                new_pos = np.dot(placement_matrix, m)
                                transforms = [new_pos.tolist()]
                            elif source_representation.RepresentationType in ['Brep']:
                                transforms = [placement_matrix.tolist()]
                            else:
                                transforms = []
                            main_obj['data']['children'].append('/' + gmsh_file)
                            main_obj['data']['children_transforms'].append(transforms)
                    except Exception as e:
                        if i.is_a('IfcFacetedBrep'):  # TODO where are MappingTarget and MappingSource?
                            try:
                                gmsh_file = id2file[i.id()]
                                transforms = []
                                main_obj['data']['children'].append('/' + gmsh_file)
                                main_obj['data']['children_transforms'].append(transforms)
                            except Exception as ee:
                                print('Error')
                                print(e)
                                print(ee)
                        else:
                            print(e)

    with open(gmsh_path / 'main.json', 'w') as f:
        json.dump(main_obj, f, indent=2)
