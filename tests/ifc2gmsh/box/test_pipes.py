"""
https://wiki.osarch.org/index.php?title=IfcOpenShell_code_examples
"""

from pprint import pprint

import ifcopenshell
import time
import uuid


def create_ifcaxis2placement(ifcfile, point=(0., 0., 0.),
                             dir1=(0., 0., 1.),
                             dir2=(1., 0., 0.)):
    point = ifcfile.createIfcCartesianPoint(point)
    dir1 = ifcfile.createIfcDirection(dir1)
    dir2 = ifcfile.createIfcDirection(dir2)
    axis2placement = ifcfile.createIfcAxis2Placement3D(point, dir1, dir2)
    return axis2placement


def create_ifclocalplacement(ifcfile, point=(0., 0., 0.),
                             dir1=(0., 0., 1.), dir2=(1., 0., 0.),
                             relative_to=None):
    axis2placement = create_ifcaxis2placement(ifcfile, point, dir1, dir2)
    ifclocalplacement2 = ifcfile.createIfcLocalPlacement(relative_to, axis2placement)
    return ifclocalplacement2

# Creates an IfcPolyLine from a list of points, specified as Python tuples
def create_ifcpolyline(ifcfile, point_list):
    ifcpts = []
    for point in point_list:
        point = ifcfile.createIfcCartesianPoint(point)
        ifcpts.append(point)
    polyline = ifcfile.createIfcPolyLine(ifcpts)
    return polyline


def create_ifcextrudedareasolid(ifcfile, point_list, ifcaxis2placement, extrude_dir, extrusion):
    polyline = create_ifcpolyline(ifcfile, point_list)
    ifcclosedprofile = ifcfile.createIfcArbitraryClosedProfileDef("AREA", None, polyline)
    ifcdir = ifcfile.createIfcDirection(extrude_dir)
    ifcextrudedareasolid = ifcfile.createIfcExtrudedAreaSolid(ifcclosedprofile, ifcaxis2placement, ifcdir, extrusion)
    return ifcextrudedareasolid

create_guid = lambda: ifcopenshell.guid.compress(uuid.uuid1().hex)


def test_pipes(request, monkeypatch):
    monkeypatch.chdir(request.fspath.dirname)

    filename = "pipes.ifc"
    timestamp = time.time()
    timestring = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(timestamp))
    creator = "Kianwee Chen"
    organization = "NUS"
    application, application_version = "IfcOpenShell", "0.5"
    project_globalid, project_name = create_guid(), "Hello Wall"
    schema = ifcopenshell.ifcopenshell_wrapper.schema_by_name("IFC2x3")

    # A template IFC file to quickly populate entity instances for an IfcProject with its dependencies

    template = """ISO-10303-21;
    HEADER;
    FILE_DESCRIPTION(('ViewDefinition [CoordinationView]'),'2;1');
    FILE_NAME('%(filename)s','%(timestring)s',('%(creator)s'),('%(organization)s'),'%(application)s','%(application)s','');
    FILE_SCHEMA(('IFC2X3'));
    ENDSEC;
    DATA;
    #1=IFCPERSON($,$,'%(creator)s',$,$,$,$,$);
    #2=IFCORGANIZATION($,'%(organization)s',$,$,$);
    #3=IFCPERSONANDORGANIZATION(#1,#2,$);
    #4=IFCAPPLICATION(#2,'%(application_version)s','%(application)s','');
    #5=IFCOWNERHISTORY(#3,#4,$,.ADDED.,$,#3,#4,%(timestamp)s);
    #6=IFCDIRECTION((1.,0.,0.));
    #7=IFCDIRECTION((0.,0.,1.));
    #8=IFCCARTESIANPOINT((0.,0.,0.));
    #9=IFCAXIS2PLACEMENT3D(#8,#7,#6);
    #10=IFCDIRECTION((0.,1.,0.));
    #11=IFCGEOMETRICREPRESENTATIONCONTEXT($,'Model',3,1.E-05,#9,#10);
    #12=IFCDIMENSIONALEXPONENTS(0,0,0,0,0,0,0);
    #13=IFCSIUNIT(\*,.LENGTHUNIT.,$,.METRE.);
    #14=IFCSIUNIT(\*,.AREAUNIT.,$,.SQUARE_METRE.);
    #15=IFCSIUNIT(\*,.VOLUMEUNIT.,$,.CUBIC_METRE.);
    #16=IFCSIUNIT(\*,.PLANEANGLEUNIT.,$,.RADIAN.);
    #17=IFCMEASUREWITHUNIT(IFCPLANEANGLEMEASURE(0.017453292519943295),#16);
    #18=IFCCONVERSIONBASEDUNIT(#12,.PLANEANGLEUNIT.,'DEGREE',#17);
    #19=IFCUNITASSIGNMENT((#13,#14,#15,#18));
    #20=IFCPROJECT('%(project_globalid)s',#5,'%(project_name)s',$,$,$,$,(#11),#19);
    ENDSEC;
    END-ISO-10303-21;
    """ % locals()

    with open(filename, "w") as f:
        f.write(template)

    ifc = ifcopenshell.open(filename)
    owner_history = ifc.by_type("IfcOwnerHistory")[0]
    project = ifc.by_type("IfcProject")[0]
    context = ifc.by_type("IfcGeometricRepresentationContext")[0]
    site_placement = create_ifclocalplacement(ifc)
    pprint(schema.declaration_by_name('IfcSite').all_attributes())
    site = ifc.createIfcSite(ifcopenshell.guid.new(),
                             owner_history, "Site", None, None,
                             site_placement, None, None,
                             "ELEMENT", None, None,
                             None, None, None)
    container_project = ifc.createIfcRelAggregates(
        create_guid(), owner_history, "Project Container",
        None, project, [site])
    building_placement = create_ifclocalplacement(ifc, relative_to=site_placement)
    building = ifc.createIfcBuilding(ifcopenshell.guid.new(),
                                     owner_history, 'Building', None,
                                     None, building_placement, None, None,
                                     "ELEMENT", None, None, None)
    container_site = ifc.createIfcRelAggregates(create_guid(),
                                                owner_history,
                                                "Site Container", None, site,
                                                [building])
    # storey_placement = create_ifclocalplacement(ifc, relative_to=building_placement)
    # elevation = 0.0
    # building_storey = ifc.createIfcBuildingStorey(create_guid(), owner_history,
    #                                                   'Storey', None, None,
    #                                                   storey_placement, None, None,
    #                                                   "ELEMENT", elevation)

    # At least one product should exist?
    pprint(schema.declaration_by_name('IfcProduct').all_attributes())
    attr = schema.declaration_by_name('IfcPipeSegmentType').all_attributes()

    ps = ifc.createIfcPipeSegmentType(
        ifcopenshell.guid.new(), owner_history, "Name", "Description",
        None, None, None, None, None, 'RIGIDSEGMENT')

    ifc.write(filename)

    # product_placement = create_ifclocalplacement(ifc, relative_to=site_placement)
    # product = ifc.createIfcProduct(
    #     ifcopenshell.guid.new(), owner_history, "Name", "Description", "Type",
    #     product_placement, None)
    # pprint(product)

    # https://thinkmoult.com/using-ifcopenshell-parse-ifc-files-python.html
    # https://wiki.osarch.org/index.php?title=IfcOpenShell_code_examples
    # https://community.osarch.org/discussion/711/ifcopenshell-how-to-add-a-new-property-and-value-to-an-object
    # ifc = ifcopenshell.open('box_2.ifc')
    # owner_history = ifc.by_type("IfcOwnerHistory")[0]
    # project = ifc.by_type("IfcProject")[0]
    # context = ifc.by_type("IfcGeometricRepresentationContext")[0]
    # print(project)
    # print(context)
    # print(owner_history)
    # products = ifc.by_type('IfcProduct')
    # print(f'products: {len(products)}')

    # ifc.createIfcPipeSegment()
    # schema = ifcopenshell.ifcopenshell_wrapper.schema_by_name("IFC2x3")
    # # ps = schema.declaration_by_name('IfcPipeSegment')
    # # ps = schema.declaration_by_name('IfcPipeFittingType')
    # ps = schema.declaration_by_name('IfcPipeSegmentType')
    # pprint(ps.all_attributes())

    # https://ifcopenshell.github.io/docs/rst_files/class_ifc2x3_1_1_ifc_property_single_value.html#exhale-class-class-ifc2x3-1-1-ifc-property-single-value
    # https://ifcopenshell.github.io/docs/rst_files/class_ifc2x3_1_1_ifc_integer.html#exhale-class-class-ifc2x3-1-1-ifc-integer
    # https://ifcopenshell.github.io/docs/rst_files/struct_ifc2x3.html#_CPPv4N6Ifc2x38IfcValueE
    # https://ifcopenshell.github.io/docs/rst_files/class_ifc2x3_1_1_ifc_text.html#exhale-class-class-ifc2x3-1-1-ifc-text
    # https://ifcopenshell.github.io/docs/rst_files/struct_ifc2x3.html#_CPPv4N6Ifc2x37IfcUnitE
    # gmsh_properties = [
    #     ifc.createIfcPropertySingleValue(
    #         "BooleanLevel",  # Name
    #         "Level for boolean operations before meshing",  # Description
    #         ifc.createIfcInteger(1),  # NominalValue
    #         None  # Unit
    #     ),
    #     ifc.createIfcPropertySingleValue(
    #         "Zone",  # Name
    #         "Name for mesh zone",  # Description
    #         ifc.createIfcText('TestZone'),  # Value
    #         None  # Unit
    #     )
    # ]
    # # https://ifcopenshell.github.io/docs/rst_files/class_ifc2x3_1_1_ifc_property_set.html
    # gmsh_property_set = ifc.createIfcPropertySet(
    #     ifcopenshell.guid.new(),  # GlobalId
    #     owner_history,  # OwnerHistory
    #     "IBRAE_GmshScriptsProperties",  # Name
    #     "Properties for mesh generator "
    #     "gmsh-scripts https://github.com/romanzes637/gmsh_scripts",  #  Description
    #     gmsh_properties  # HasProperties
    # )
    # # https://ifcopenshell.github.io/docs/rst_files/class_ifc2x3_1_1_ifc_rel_defines_by_properties.html
    # ifc.createIfcRelDefinesByProperties(
    #     ifcopenshell.guid.new(),  # GlobalId
    #     owner_history,  # OwnerHistory
    #     None,  # Name
    #     None,  # Description
    #     products,  # RelatedObjects
    #     gmsh_property_set  # RelatingPropertyDefinition
    # )
    #
    # # https://ifcopenshell.github.io/docs/rst_files/class_ifc2x3_1_1_ifc_element_quantity.html
    # # https://ifcopenshell.github.io/docs/rst_files/class_ifc2x3_1_1_ifc_physical_quantity.html#_CPPv4N6Ifc2x319IfcPhysicalQuantityE
    # # https://ifcopenshell.github.io/docs/rst_files/struct_ifc2x3.html#class_ifc2x3_1_1_ifc_physical_simple_quantity
    # # https://standards.buildingsmart.org/IFC/DEV/IFC4_3/RC1/HTML/schema/ifcquantityresource/lexical/ifcphysicalsimplequantity.htm
    # # https://ifcopenshell.github.io/docs/rst_files/struct_ifc2x3.html#_CPPv4N6Ifc2x311IfcUnitEnumE
    # # https://ifcopenshell.github.io/docs/rst_files/struct_ifc2x3.html#_CPPv4N6Ifc2x311IfcSIPrefixE
    # # https://ifcopenshell.github.io/docs/rst_files/struct_ifc2x3.html#_CPPv4N6Ifc2x313IfcSIUnitNameE
    # # https://wiki.osarch.org/index.php?title=IfcOpenShell_code_examples#Exploring_IFC_schema
    #
    # # Workaround of python enum see https://forum.freecadweb.org/viewtopic.php?style=4&t=15582
    # schema = ifcopenshell.ifcopenshell_wrapper.schema_by_name("IFC2x3")
    # si_unit = schema.declaration_by_name('IfcSIUnit')
    # pprint(si_unit.all_attributes())
    # cubic_meter = ifc.createIfcSIUnit()
    # cubic_meter.UnitType = "VOLUMEUNIT"
    # cubic_meter.Prefix = None
    # cubic_meter.Name = "CUBIC_METRE"
    # fenia_quantities = [
    #     ifc.createIfcQuantityVolume(
    #         "Volume",  # Name
    #         "Volume of the element",  # Description
    #         cubic_meter,  # Unit
    #         42  # VolumeValue
    #     )
    # ]
    # fenia_element_quantity = ifc.createIfcElementQuantity(
    #     ifcopenshell.guid.new(),  # GlobalId
    #     owner_history,  # OwnerHistory
    #     "IBRAE_FeniaQuantities",  # Name
    #     "Quantities of FENIA code",  # Description
    #     None,  # MethodOfMeasurement
    #     fenia_quantities  # Quantities
    # )
    # ifc.createIfcRelDefinesByProperties(
    #     ifcopenshell.guid.new(),  # GlobalId
    #     owner_history,  # OwnerHistory
    #     None,  # Name
    #     None,  # Description
    #     products,  # RelatedObjects
    #     fenia_element_quantity  # RelatingPropertyDefinition
    # )
    # ifc.write('box_with_properties.ifc')
    #
    # ifc = ifcopenshell.open('box_with_properties.ifc')
    # products = ifc.by_type('IfcProduct')
    # cnt = 0
    # for product in products:
    #     if product.GlobalId == '2wGebYoZr8CujW8_P1W8tC':
    #         print(product.get_info())
    #         for x in product.IsDefinedBy:
    #             if hasattr(x, 'RelatingPropertyDefinition'):
    #                 # if x.RelatingPropertyDefinition.is_a('IfcElementQuantity'):
    #                 #     print()
    #                 #     pprint(x.RelatingPropertyDefinition.Name)
    #                 #     for y in x.RelatingPropertyDefinition.Quantities:
    #                 #         pprint(y.Name)
    #                 if x.RelatingPropertyDefinition.is_a('IfcPropertySet'):
    #                     cnt += 1
    #                     print()
    #                     pprint(f'{cnt}. {x.RelatingPropertyDefinition.Name}')
    #                     for y in x.RelatingPropertyDefinition.HasProperties:
    #                         pprint(y.get_info())
