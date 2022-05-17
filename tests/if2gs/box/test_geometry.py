from collections import Counter, deque
from pprint import pprint
import json

import ifcopenshell
import gmsh


def polyloops_to_volume(outer, points_tags, curves_pairs, surfaces_curves):
    print(outer.is_a())
    ss = []
    print(len(outer.CfsFaces))
    for fi, f in enumerate(outer.CfsFaces):
        # print(f)
        polyloops = [x.Bound for x in f.Bounds]
        n_duplicated_pairs = 0
        n_reversed_pairs = 0
        # curve_loops_tags = set()
        # print(len(polyloops))
        for pl in polyloops:
            pg = pl.Polygon
            tags = deque()
            curve_tags = []
            for i, p in enumerate(pg):
                # print(p.get_info())
                cs = p.Coordinates
                tag = p.id()
                tags.append(tag)
                # print(dir(p))
                if tag not in points_tags:
                    points_tags.add(tag)
                    gmsh.model.geo.addPoint(x=cs[0], y=cs[1], z=cs[2], tag=tag)
            for _ in range(len(tags)):
                pair, rev_pair = (tags[0], tags[1]), (tags[1], tags[0])
                if pair in curves_pairs:
                    lt = curves_pairs[pair]
                    n_duplicated_pairs += 1
                elif rev_pair in curves_pairs:
                    lt = -curves_pairs[rev_pair]
                    n_reversed_pairs += 1
                else:
                    lt = gmsh.model.geo.addLine(startTag=pair[0], endTag=pair[1])
                    curves_pairs[pair] = lt
                curve_tags.append(lt)
                tags.rotate(-1)
            clt = gmsh.model.geo.addCurveLoop(curveTags=curve_tags)
            st = gmsh.model.geo.addPlaneSurface(wireTags=[clt])
            ss.append(st)
    slt = gmsh.model.geo.addSurfaceLoop(ss, outer.id())
    vt = gmsh.model.geo.addVolume([slt], outer.id())
    gmsh.model.geo.synchronize()
    gmsh.model.addPhysicalGroup(2, ss, name=f"S{outer.id()}")
    gmsh.model.addPhysicalGroup(3, [vt], name=f"V{outer.id()}")


def test_geometry(request, monkeypatch):
    monkeypatch.chdir(request.fspath.dirname)

    ifc = ifcopenshell.open('box.ifc')
    owner_history = ifc.by_type("IfcOwnerHistory")[0]
    project = ifc.by_type("IfcProject")[0]
    context = ifc.by_type("IfcGeometricRepresentationContext")[0]
    print(ifc.by_type("IfcOwnerHistory"))

    products = ifc.by_type('IfcProduct')
    print(f'products: {len(products)}')
    shapes = ifc.by_type('IfcShapeRepresentation')
    print(f'shapes: {len(shapes)}')
    pprint(Counter([x.RepresentationIdentifier for x in shapes]))
    pprint(Counter([x.RepresentationType for x in shapes]))
    pprint(Counter([x.is_a() for x in products]))

    gmsh.initialize()
    gmsh.model.add("box")
    points_tags = set()
    curves_points = dict()
    surfaces_curves = dict()
    # for i, shape in enumerate(shapes):
    #     print(f'\n{i + 1}. {shape.RepresentationType}')
    #     if shape.RepresentationType == 'Brep':
    #         pass
    #         # print(shape.get_info())
    #         # for item in shape.Items:  # IfcFacetedBrep
    #         #     # print(item.get_info())
    #         #     polyloops_to_volume(item.Outer, points_tags,
    #         #                         curves_points, surfaces_curves)
    #     elif shape.RepresentationType == 'SweptSolid':
    #         pass
    #         # print(shape.get_info())
    #         # for item in shape.Items:  # IfcExtrudedAreaSolid
    #         #     if item.is_a('IfcExtrudedAreaSolid'):
    #         #         if item.SweptArea.is_a('IfcCircleHollowProfileDef'):
    #         #             print(item.get_info())
    #         #             print(item.SweptArea.get_info())
    #         #             r1 = item.SweptArea.Radius
    #         #             r2 = item.SweptArea.Radius + item.SweptArea.WallThickness
    #         #             h = item.Depth
    #         #             z1, z2 = f"V{item.id()}_1", f"V{item.id()}_2"
    #         #             gs_input = {
    #         #                 "data": {
    #         #                     "class": "block.Layer",
    #         #                     "layer": [[r1, r2], [h]],
    #         #                     "layer_curves": [["circle_arc", "circle_arc"], ["line"]],
    #         #                     "items_zone": [z1, z2],
    #         #                     "items_boolean_level_map": 0,
    #         #                     "transforms": [[0, 0, 0]]}}
    #         #             with open(f'V{item.id()}.json', 'w') as f:
    #         #                 json.dump(gs_input, f, indent=2)
    #     elif shape.RepresentationType == 'MappedRepresentation':
    #         print(shape.get_info())
    #         pprint([x.get_info() for x in ifc.get_inverse(shape)])
    #         # for item in shape.Items:  # IfcExtrudedAreaSolid
    #         #     print(item.get_info())
    #         #     print(item.MappingSource.get_info())
    #         #     print(item.MappingSource.MappedRepresentation.get_info())
    #     elif shape.RepresentationType == 'GeometricCurveSet':
    #         pass
    #         # print(shape.get_info())
    #         # pprint([x.get_info() for x in ifc.get_inverse(shape)])
    #         # for item in shape.Items:  # IfcGeometricCurveSet
    #         #     print(item.get_info())
    #         #     for element in item.Elements:
    #         #         print(element.get_info())
    gmsh.model.geo.synchronize()
    gmsh.write("box.geo_unrolled")
    gmsh.finalize()

