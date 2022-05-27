from pprint import pprint

import ifcopenshell


def test_properties(request, monkeypatch):
    monkeypatch.chdir(request.fspath.dirname)
    # https://thinkmoult.com/using-ifcopenshell-parse-ifc-files-python.html
    # https://wiki.osarch.org/index.php?title=IfcOpenShell_code_examples
    # https://community.osarch.org/discussion/711/ifcopenshell-how-to-add-a-new-property-and-value-to-an-object
    ifc = ifcopenshell.open('box_2.ifc')
    owner_history = ifc.by_type("IfcOwnerHistory")[0]
    project = ifc.by_type("IfcProject")[0]
    context = ifc.by_type("IfcGeometricRepresentationContext")[0]
    print(project)
    print(context)
    print(owner_history)
    products = ifc.by_type('IfcProduct')
    print(f'products: {len(products)}')

    # https://ifcopenshell.github.io/docs/rst_files/class_ifc2x3_1_1_ifc_property_single_value.html#exhale-class-class-ifc2x3-1-1-ifc-property-single-value
    # https://ifcopenshell.github.io/docs/rst_files/class_ifc2x3_1_1_ifc_integer.html#exhale-class-class-ifc2x3-1-1-ifc-integer
    # https://ifcopenshell.github.io/docs/rst_files/struct_ifc2x3.html#_CPPv4N6Ifc2x38IfcValueE
    # https://ifcopenshell.github.io/docs/rst_files/class_ifc2x3_1_1_ifc_text.html#exhale-class-class-ifc2x3-1-1-ifc-text
    # https://ifcopenshell.github.io/docs/rst_files/struct_ifc2x3.html#_CPPv4N6Ifc2x37IfcUnitE
    gmsh_properties = [
        ifc.createIfcPropertySingleValue(
            "BooleanLevel",  # Name
            "Level for boolean operations before meshing",  # Description
            ifc.createIfcInteger(1),  # NominalValue
            None  # Unit
        ),
        ifc.createIfcPropertySingleValue(
            "Zone",  # Name
            "Name for mesh zone",  # Description
            ifc.createIfcText('TestZone'),  # Value
            None  # Unit
        )
    ]
    # https://ifcopenshell.github.io/docs/rst_files/class_ifc2x3_1_1_ifc_property_set.html
    gmsh_property_set = ifc.createIfcPropertySet(
        ifcopenshell.guid.new(),  # GlobalId
        owner_history,  # OwnerHistory
        "IBRAE_GmshScriptsProperties",  # Name
        "Properties for mesh generator "
        "gmsh-scripts https://github.com/romanzes637/gmsh_scripts",  #  Description
        gmsh_properties  # HasProperties
    )
    # https://ifcopenshell.github.io/docs/rst_files/class_ifc2x3_1_1_ifc_rel_defines_by_properties.html
    ifc.createIfcRelDefinesByProperties(
        ifcopenshell.guid.new(),  # GlobalId
        owner_history,  # OwnerHistory
        None,  # Name
        None,  # Description
        products,  # RelatedObjects
        gmsh_property_set  # RelatingPropertyDefinition
    )

    # https://ifcopenshell.github.io/docs/rst_files/class_ifc2x3_1_1_ifc_element_quantity.html
    # https://ifcopenshell.github.io/docs/rst_files/class_ifc2x3_1_1_ifc_physical_quantity.html#_CPPv4N6Ifc2x319IfcPhysicalQuantityE
    # https://ifcopenshell.github.io/docs/rst_files/struct_ifc2x3.html#class_ifc2x3_1_1_ifc_physical_simple_quantity
    # https://standards.buildingsmart.org/IFC/DEV/IFC4_3/RC1/HTML/schema/ifcquantityresource/lexical/ifcphysicalsimplequantity.htm
    # https://ifcopenshell.github.io/docs/rst_files/struct_ifc2x3.html#_CPPv4N6Ifc2x311IfcUnitEnumE
    # https://ifcopenshell.github.io/docs/rst_files/struct_ifc2x3.html#_CPPv4N6Ifc2x311IfcSIPrefixE
    # https://ifcopenshell.github.io/docs/rst_files/struct_ifc2x3.html#_CPPv4N6Ifc2x313IfcSIUnitNameE
    # https://wiki.osarch.org/index.php?title=IfcOpenShell_code_examples#Exploring_IFC_schema

    # Workaround of python enum see https://forum.freecadweb.org/viewtopic.php?style=4&t=15582
    schema = ifcopenshell.ifcopenshell_wrapper.schema_by_name("IFC2x3")
    si_unit = schema.declaration_by_name('IfcSIUnit')
    pprint(si_unit.all_attributes())
    cubic_meter = ifc.createIfcSIUnit()
    cubic_meter.UnitType = "VOLUMEUNIT"
    cubic_meter.Prefix = None
    cubic_meter.Name = "CUBIC_METRE"
    fenia_quantities = [
        ifc.createIfcQuantityVolume(
            "Volume",  # Name
            "Volume of the element",  # Description
            cubic_meter,  # Unit
            42  # VolumeValue
        )
    ]
    fenia_element_quantity = ifc.createIfcElementQuantity(
        ifcopenshell.guid.new(),  # GlobalId
        owner_history,  # OwnerHistory
        "IBRAE_FeniaQuantities",  # Name
        "Quantities of FENIA code",  # Description
        None,  # MethodOfMeasurement
        fenia_quantities  # Quantities
    )
    ifc.createIfcRelDefinesByProperties(
        ifcopenshell.guid.new(),  # GlobalId
        owner_history,  # OwnerHistory
        None,  # Name
        None,  # Description
        products,  # RelatedObjects
        fenia_element_quantity  # RelatingPropertyDefinition
    )
    ifc.write('box_with_properties.ifc')

    ifc = ifcopenshell.open('box_with_properties.ifc')
    products = ifc.by_type('IfcProduct')
    cnt = 0
    for product in products:
        if product.GlobalId == '2wGebYoZr8CujW8_P1W8tC':
            print(product.get_info())
            for x in product.IsDefinedBy:
                if hasattr(x, 'RelatingPropertyDefinition'):
                    # if x.RelatingPropertyDefinition.is_a('IfcElementQuantity'):
                    #     print()
                    #     pprint(x.RelatingPropertyDefinition.Name)
                    #     for y in x.RelatingPropertyDefinition.Quantities:
                    #         pprint(y.Name)
                    if x.RelatingPropertyDefinition.is_a('IfcPropertySet'):
                        cnt += 1
                        print()
                        pprint(f'{cnt}. {x.RelatingPropertyDefinition.Name}')
                        for y in x.RelatingPropertyDefinition.HasProperties:
                            pprint(y.get_info())
