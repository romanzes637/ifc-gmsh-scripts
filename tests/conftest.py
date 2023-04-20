import logging

import pytest
import ifcopenshell

from ifcopenshell.validate import validate, json_logger


@pytest.fixture(autouse=True)
def change_test_dir(request, monkeypatch):
    monkeypatch.chdir(request.fspath.dirname)


@pytest.fixture(autouse=True)
def create_box_with_properties(box_path='box.ifc',
                               box_props_path='box_with_properties.ifc'):
    """
    See also:
        * https://thinkmoult.com/using-ifcopenshell-parse-ifc-files-python.html
        * https://wiki.osarch.org/index.php?title=IfcOpenShell_code_examples
        * https://community.osarch.org/discussion/711/ifcopenshell-how-to-add-a-new-property-and-value-to-an-object
    """
    print('Executing create_box_with_properties')
    print(f'Reading {box_path}')
    model = ifcopenshell.open(box_path)
    schema = model.schema
    owner_history = model.by_type("IfcOwnerHistory")[0]
    project = model.by_type("IfcProject")[0]
    context = model.by_type("IfcGeometricRepresentationContext")[0]
    print(f'IFC schema {schema}')
    print(f'IFC project {project}')
    print(f'IFC context {context}')
    print(f'IFC owner_history {owner_history}')
    products = model.by_type('IfcProduct')
    print(f'Number of products: {len(products)}')

    # Zone name
    volume_zones_property = model.create_entity(
        type='IfcPropertyListValue',
        Name="VolumeZones",
        ListValues=[model.create_entity(type='IfcIdentifier', wrappedValue='Zone1')])
    surfaces_zone_property = model.create_entity(
        type='IfcPropertyListValue',
        Name="SurfacesZones",
        ListValues=[
            model.create_entity(type='IfcIdentifier', wrappedValue='Surface1'),
            model.create_entity(type='IfcIdentifier', wrappedValue='Surface2'),
            model.create_entity(type='IfcIdentifier', wrappedValue='Surface3'),
            model.create_entity(type='IfcIdentifier', wrappedValue='Surface4'),
            model.create_entity(type='IfcIdentifier', wrappedValue='Surface5'),
            model.create_entity(type='IfcIdentifier', wrappedValue='Surface6')])

    print('Creating gmsh properties')
    gmsh_properties = [
        model.create_entity(
            type='IfcPropertySingleValue',
            Name="BooleanLevel",
            Description="Level for boolean operations before meshing",
            NominalValue=model.create_entity(type='IfcInteger', wrappedValue=0),
            Unit=None),
        volume_zones_property,
        surfaces_zone_property]
    gmsh_property_set = model.create_entity(
        type='IfcPropertySet',
        GlobalId=ifcopenshell.guid.new(),
        OwnerHistory=owner_history,
        Name="IBRAE_Gmsh",
        Description="Properties for mesh generator. See https://github.com/romanzes637/gmsh_scripts",
        HasProperties=gmsh_properties)

    model.create_entity(
        type='IfcRelDefinesByProperties',
        GlobalId=ifcopenshell.guid.new(),
        OwnerHistory=owner_history,
        Name=None,
        Description=None,
        RelatedObjects=products,
        RelatingPropertyDefinition=gmsh_property_set)

    print('Creating FENIA properties')
    # Material properties
    density = model.create_entity(type='IfcReal', wrappedValue=1000.0)
    density_unit = model.create_entity(
        type='IfcDerivedUnit',
        Elements=[
            model.create_entity(
                type='IfcDerivedUnitElement',
                Exponent=1,
                Unit=model.create_entity('IfcSIUnit', Name='GRAM', Prefix='KILO')),
            model.create_entity(
                type='IfcDerivedUnitElement',
                Exponent=-3,
                Unit=model.create_entity('IfcSIUnit', Name='METRE', Prefix=None))],
        UnitType='MASSDENSITYUNIT')
    thermal_conductivity = model.create_entity(type='IfcReal', wrappedValue=1.8)
    thermal_conductivity_unit = model.create_entity(
        type='IfcDerivedUnit',
        Elements=[
            model.create_entity(
                type='IfcDerivedUnitElement',
                Exponent=1,
                Unit=model.create_entity('IfcSIUnit', Name='WATT', Prefix=None)),
            model.create_entity(
                type='IfcDerivedUnitElement',
                Exponent=-1,
                Unit=model.create_entity('IfcSIUnit', Name='METRE', Prefix=None)),
            model.create_entity(
                type='IfcDerivedUnitElement',
                Exponent=-1,
                Unit=model.create_entity('IfcSIUnit', Name='KELVIN', Prefix=None))],
        UnitType='THERMALCONDUCTANCEUNIT')
    specific_heat_capacity = model.create_entity(type='IfcReal', wrappedValue=1000)
    specific_heat_capacity_unit = model.create_entity(
        type='IfcDerivedUnit',
        Elements=[
            model.create_entity(
                type='IfcDerivedUnitElement',
                Exponent=1,
                Unit=model.create_entity('IfcSIUnit', Name='JOULE', Prefix=None)),
            model.create_entity(
                type='IfcDerivedUnitElement',
                Exponent=1,
                Unit=model.create_entity('IfcSIUnit', Name='GRAM', Prefix='KILO')),
            model.create_entity(
                type='IfcDerivedUnitElement',
                Exponent=-1,
                Unit=model.create_entity('IfcSIUnit', Name='KELVIN', Prefix=None))],
        UnitType='SPECIFICHEATCAPACITYUNIT')
    volumetric_heat_source = model.create_entity(type='IfcReal', wrappedValue=1)
    volumetric_heat_source_unit = model.create_entity(
        type='IfcDerivedUnit',
        Elements=[
            model.create_entity(
                type='IfcDerivedUnitElement',
                Exponent=1,
                Unit=model.create_entity('IfcSIUnit', Name='WATT', Prefix=None)),
            model.create_entity(
                type='IfcDerivedUnitElement',
                Exponent=-3,
                Unit=model.create_entity('IfcSIUnit', Name='METRE', Prefix=None))],
        UnitType='HEATINGVALUEUNIT')
    material_type = model.create_entity(type='IfcIdentifier', wrappedValue="constPropTSource")
    material_property = model.create_entity(
        type='IfcComplexProperty',
        Name="MaterialProperty",
        UsageName='Zone1',  # Should be IfcIdentifier!
        Description=None,
        HasProperties=[
            model.create_entity(
                type='IfcPropertySingleValue',
                Name="matType",
                Description=None,
                NominalValue=material_type,
                Unit=None),
            model.create_entity(
                type='IfcPropertySingleValue',
                Name="rho",
                Description=None,
                NominalValue=density,
                Unit=density_unit),
            model.create_entity(
                type='IfcPropertySingleValue',
                Name="DT",
                Description=None,
                NominalValue=thermal_conductivity,
                Unit=thermal_conductivity_unit),
            model.create_entity(
                type='IfcPropertySingleValue',
                Name="cHeat",
                Description=None,
                NominalValue=specific_heat_capacity,
                Unit=specific_heat_capacity_unit),
            model.create_entity(
                type='IfcPropertySingleValue',
                Name="qW",
                Description=None,
                NominalValue=volumetric_heat_source,
                Unit=volumetric_heat_source_unit)])

    # Initial conditions
    initial_condition_condition_type = model.create_entity(type='IfcIdentifier', wrappedValue="temperature")
    initial_condition_type_property = model.create_entity(
        type='IfcPropertySingleValue',
        Name="type",
        Description=None,
        NominalValue=initial_condition_condition_type,
        Unit=None)
    initial_condition_temperature = model.create_entity(type='IfcReal', wrappedValue=100.0)
    initial_condition_temperature_unit = model.create_entity('IfcSIUnit', Name='KELVIN', Prefix=None)
    initial_condition_temperature_property = model.create_entity(
        type='IfcPropertySingleValue',
        Name="inZoneTemperature",
        Description=None,
        NominalValue=initial_condition_temperature,
        Unit=initial_condition_temperature_unit)
    initial_condition_property = model.create_entity(
        type='IfcComplexProperty',
        Name="InitialCondition",
        UsageName='Zone1',  # Should be IfcIdentifier!
        Description=None,
        HasProperties=[initial_condition_type_property,
                       initial_condition_temperature_property])

    # Boundary conditions
    # Surface1
    boundary_condition_1_type = model.create_entity(type='IfcIdentifier', wrappedValue="timeValueTr")
    boundary_condition_1_type_property = model.create_entity(
        type='IfcPropertySingleValue',
        Name="type",
        Description=None,
        NominalValue=boundary_condition_1_type,
        Unit=None)
    boundary_condition_1_temperature = model.create_entity(type='IfcReal', wrappedValue=273.0)
    boundary_condition_1_temperature_unit = model.create_entity('IfcSIUnit', Name='KELVIN', Prefix=None)
    boundary_condition_1_temperature_property = model.create_entity(
        type='IfcPropertySingleValue',
        Name="timeValueTr",
        Description=None,
        NominalValue=boundary_condition_1_temperature,
        Unit=boundary_condition_1_temperature_unit)
    boundary_condition_1_property = model.create_entity(
        type='IfcComplexProperty',
        Name="BoundaryCondition",
        UsageName='Surface1',  # Should be IfcIdentifier!
        Description=None,
        HasProperties=[boundary_condition_1_type_property,
                       boundary_condition_1_temperature_property])

    # Surface2
    boundary_condition_2_type = model.create_entity(type='IfcIdentifier', wrappedValue="timeValueTr")
    boundary_condition_2_type_property = model.create_entity(
        type='IfcPropertySingleValue',
        Name="type",
        Description=None,
        NominalValue=boundary_condition_2_type,
        Unit=None)
    boundary_condition_2_temperature = model.create_entity(type='IfcReal', wrappedValue=300.0)
    boundary_condition_2_temperature_unit = model.create_entity('IfcSIUnit', Name='KELVIN', Prefix=None)
    boundary_condition_2_temperature_property = model.create_entity(
        type='IfcPropertySingleValue',
        Name="timeValueTr",
        Description=None,
        NominalValue=boundary_condition_2_temperature,
        Unit=boundary_condition_2_temperature_unit)
    boundary_condition_2_property = model.create_entity(
        type='IfcComplexProperty',
        Name="BoundaryCondition",
        UsageName='Surface2',  # Should be IfcIdentifier!
        Description=None,
        HasProperties=[boundary_condition_2_type_property,
                       boundary_condition_2_temperature_property])

    # Surface3
    boundary_condition_3_type = model.create_entity(type='IfcIdentifier', wrappedValue="fixedFlux")
    boundary_condition_3_type_property = model.create_entity(
        type='IfcPropertySingleValue',
        Name="type",
        Description=None,
        NominalValue=boundary_condition_3_type,
        Unit=None)
    boundary_condition_3_heat_flux = model.create_entity(type='IfcReal', wrappedValue=10.0)
    boundary_condition_3_heat_flux_unit = model.create_entity(
        type='IfcDerivedUnit',
        Elements=[
            model.create_entity(
                type='IfcDerivedUnitElement',
                Exponent=1,
                Unit=model.create_entity('IfcSIUnit', Name='WATT', Prefix=None)),
            model.create_entity(
                type='IfcDerivedUnitElement',
                Exponent=-2,
                Unit=model.create_entity('IfcSIUnit', Name='METRE', Prefix=None))],
        UnitType='HEATFLUXDENSITYUNIT')
    boundary_condition_3_heat_flux_property = model.create_entity(
        type='IfcPropertySingleValue',
        Name="fluxValue",
        Description=None,
        NominalValue=boundary_condition_3_heat_flux,
        Unit=boundary_condition_3_heat_flux_unit)
    boundary_condition_3_property = model.create_entity(
        type='IfcComplexProperty',
        Name="BoundaryCondition",
        UsageName='Surface3',  # Should be IfcIdentifier!
        Description=None,
        HasProperties=[boundary_condition_3_type_property,
                       boundary_condition_3_heat_flux_property])

    # Surface4
    boundary_condition_4_type = model.create_entity(type='IfcIdentifier', wrappedValue="convectionFlux")
    boundary_condition_4_type_property = model.create_entity(
        type='IfcPropertySingleValue',
        Name="type",
        Description=None,
        NominalValue=boundary_condition_4_type,
        Unit=None)
    boundary_condition_4_temperature = model.create_entity(type='IfcReal', wrappedValue=315.0)
    boundary_condition_4_temperature_unit = model.create_entity('IfcSIUnit', Name='KELVIN', Prefix=None)
    boundary_condition_4_temperature_property = model.create_entity(
        type='IfcPropertySingleValue',
        Name="TRef",
        Description=None,
        NominalValue=boundary_condition_4_temperature,
        Unit=boundary_condition_4_temperature_unit)
    boundary_condition_4_thermal_transmittance = model.create_entity(type='IfcReal', wrappedValue=10.0)
    boundary_condition_4_thermal_transmittance_unit = model.create_entity(
        type='IfcDerivedUnit',
        Elements=[
            model.create_entity(
                type='IfcDerivedUnitElement',
                Exponent=1,
                Unit=model.create_entity('IfcSIUnit', Name='WATT', Prefix=None)),
            model.create_entity(
                type='IfcDerivedUnitElement',
                Exponent=-2,
                Unit=model.create_entity('IfcSIUnit', Name='METRE', Prefix=None)),
            model.create_entity(
                type='IfcDerivedUnitElement',
                Exponent=-1,
                Unit=model.create_entity('IfcSIUnit', Name='KELVIN', Prefix=None))],
        UnitType='THERMALTRANSMITTANCEUNIT')
    boundary_condition_4_thermal_transmittance_property = model.create_entity(
        type='IfcPropertySingleValue',
        Name="heatTrans",
        Description=None,
        NominalValue=boundary_condition_4_thermal_transmittance,
        Unit=boundary_condition_4_thermal_transmittance_unit)
    boundary_condition_4_property = model.create_entity(
        type='IfcComplexProperty',
        Name="BoundaryCondition",
        UsageName='Surface4',  # Should be IfcIdentifier!
        Description=None,
        HasProperties=[boundary_condition_4_type_property,
                       boundary_condition_4_temperature_property,
                       boundary_condition_4_thermal_transmittance_property])

    # Surface5
    boundary_condition_5_type = model.create_entity(type='IfcIdentifier', wrappedValue="timeValueTr")
    boundary_condition_5_type_property = model.create_entity(
        type='IfcPropertySingleValue',
        Name="type",
        Description=None,
        NominalValue=boundary_condition_5_type,
        Unit=None)
    boundary_condition_5_temperature = model.create_entity(type='IfcReal', wrappedValue=10.0)
    boundary_condition_5_temperature_unit = model.create_entity('IfcSIUnit', Name='KELVIN', Prefix=None)
    boundary_condition_5_temperature_property = model.create_entity(
        type='IfcPropertySingleValue',
        Name="timeValueTr",
        Description=None,
        NominalValue=boundary_condition_5_temperature,
        Unit=boundary_condition_5_temperature_unit)
    boundary_condition_5_property = model.create_entity(
        type='IfcComplexProperty',
        Name="BoundaryCondition",
        UsageName='Surface5',  # Should be IfcIdentifier!
        Description=None,
        HasProperties=[boundary_condition_5_type_property,
                       boundary_condition_5_temperature_property])

    # Surface6
    # boundary_condition_6_type = model.create_entity(type='IfcIdentifier', wrappedValue="timeValueTr")
    # boundary_condition_6_type_property = model.create_entity(
    #     type='IfcPropertySingleValue',
    #     Name="type",
    #     Description=None,
    #     NominalValue=boundary_condition_6_type,
    #     Unit=None)
    # boundary_condition_6_temperature = model.create_entity(type='IfcReal', wrappedValue=10.0)
    # boundary_condition_6_temperature_unit = model.create_entity('IfcSIUnit', Name='KELVIN', Prefix=None)
    # boundary_condition_6_temperature_property = model.create_entity(
    #     type='IfcPropertySingleValue',
    #     Name="Temperature",
    #     Description=None,
    #     NominalValue=boundary_condition_6_temperature,
    #     Unit=boundary_condition_6_temperature_unit)
    boundary_condition_6_property = model.create_entity(
        type='IfcComplexProperty',
        Name="BoundaryCondition",
        UsageName='Surface6',  # Should be IfcIdentifier!
        Description=None,
        HasProperties=[boundary_condition_5_type_property,
                       boundary_condition_5_temperature_property])

    # IfcProperty
    fenia_properties = [
        volume_zones_property,
        surfaces_zone_property,
        material_property,
        initial_condition_property,
        boundary_condition_1_property,
        boundary_condition_2_property,
        boundary_condition_3_property,
        boundary_condition_4_property,
        boundary_condition_5_property,
        boundary_condition_6_property]

    # IfcPropertySet
    fenia_property_set = model.create_entity(
        type='IfcPropertySet',
        GlobalId=ifcopenshell.guid.new(),
        OwnerHistory=owner_history,
        Name="IBRAE_Fenia",
        Description="FENIA properties",
        HasProperties=fenia_properties)

    # IfcRelDefinesByProperties
    model.create_entity(
        type='IfcRelDefinesByProperties',
        GlobalId=ifcopenshell.guid.new(),
        OwnerHistory=owner_history,
        Name=None,
        Description=None,
        RelatedObjects=products,
        RelatingPropertyDefinition=fenia_property_set)

    # print('Creating quantities')
    # # Workaround of python enum see https://forum.freecadweb.org/viewtopic.php?style=4&t=15582
    # cubic_meter = model.createIfcSIUnit()
    # cubic_meter.UnitType = "VOLUMEUNIT"
    # cubic_meter.Prefix = None
    # cubic_meter.Name = "CUBIC_METRE"
    # fenia_quantities = [
    #     model.createIfcQuantityVolume(
    #         "Volume",  # Name
    #         "Volume of the element",  # Description
    #         cubic_meter,  # Unit
    #         42  # VolumeValue
    #     )
    # ]
    # fenia_element_quantity = model.createIfcElementQuantity(
    #     ifcopenshell.guid.new(),  # GlobalId
    #     owner_history,  # OwnerHistory
    #     "IBRAE_FeniaQuantities",  # Name
    #     "Quantities of FENIA code",  # Description
    #     None,  # MethodOfMeasurement
    #     fenia_quantities  # Quantities
    # )
    # model.createIfcRelDefinesByProperties(
    #     ifcopenshell.guid.new(),  # GlobalId
    #     owner_history,  # OwnerHistory
    #     None,  # Name
    #     None,  # Description
    #     products,  # RelatedObjects
    #     fenia_element_quantity  # RelatingPropertyDefinition
    # )

    # print(f'Validating model')
    # logger = logging.getLogger("validate")
    # logger.setLevel(logging.DEBUG)
    # validate(f=model, logger=logger)

    print(f'Writing {box_props_path}')
    model.write(box_props_path)
