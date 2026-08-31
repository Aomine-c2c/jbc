"""
Department-specific configurable field schemas for Job Reports.

Each department type has a dedicated Pydantic model with fields
relevant to that discipline's work execution records.

The `dept_specific_data` JSONB column on `JobReport` is validated
against the appropriate sub-schema based on `dept_schema_type`.

Usage:
    from app.modules.jobs.dept_schemas import validate_dept_data, DeptSchemaType

    validated = validate_dept_data("MECHANICAL", raw_dict)
"""
from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, Field


# ── Department Field Sub-schemas ──────────────────────────────


class MechanicalFields(BaseModel):
    """Fields for Mechanical Engineering department work."""
    dept_schema_type: str = "MECHANICAL"

    # Equipment identification
    machine_tag: Optional[str] = Field(None, description="Equipment tag number (e.g. PP-001)")
    machine_description: Optional[str] = Field(None, description="Full machine/equipment description")

    # Work specifics
    bearings_replaced: Optional[str] = Field(None, description="Bearing numbers and quantities replaced")
    components_replaced: Optional[str] = Field(None, description="Other components replaced or overhauled")
    lubrication_type: Optional[str] = Field(None, description="Lubricant type / grade used (e.g. Mobil DTE 24)")
    lubrication_quantity_L: Optional[float] = Field(None, description="Quantity of lubricant used in litres")

    # Measurements
    torque_specs: Optional[str] = Field(None, description="Bolt torque specifications applied")
    alignment_readings: Optional[str] = Field(None, description="Alignment readings before/after")
    vibration_readings: Optional[str] = Field(None, description="Vibration readings (mm/s RMS)")

    # Condition assessment
    condition_on_arrival: Optional[str] = Field(None, description="Physical condition when work started")
    condition_on_completion: Optional[str] = Field(None, description="Physical condition when work completed")


class InstrumentationFields(BaseModel):
    """Fields for Instrumentation & Control department work."""
    dept_schema_type: str = "INSTRUMENTATION"

    # Instrument identification
    instrument_tag: Optional[str] = Field(None, description="Instrument tag (e.g. FT-2201)")
    instrument_description: Optional[str] = Field(None, description="Full instrument description")
    instrument_manufacturer: Optional[str] = Field(None, description="Manufacturer name")
    instrument_model: Optional[str] = Field(None, description="Model number")
    instrument_serial: Optional[str] = Field(None, description="Serial number")

    # Control & process
    control_equipment: Optional[str] = Field(None, description="Control equipment involved (PLC, DCS, SCADA)")
    loop_number: Optional[str] = Field(None, description="Control loop number / P&ID reference")

    # Calibration
    calibration_performed: Optional[bool] = Field(None, description="Was calibration performed?")
    calibration_standard: Optional[str] = Field(None, description="Calibration standard / reference used")
    as_found_reading: Optional[str] = Field(None, description="Reading/output before calibration")
    as_left_reading: Optional[str] = Field(None, description="Reading/output after calibration")
    setpoint_before: Optional[str] = Field(None, description="Process setpoint before adjustment")
    setpoint_after: Optional[str] = Field(None, description="Process setpoint after adjustment")

    # Cable & signal
    cable_type: Optional[str] = Field(None, description="Signal cable type (4-20mA, HART, Profibus, etc.)")
    sensor_type: Optional[str] = Field(None, description="Sensor type replaced or worked on")


class ITSystemsFields(BaseModel):
    """Fields for IT Systems / ICT department work."""
    dept_schema_type: str = "IT_SYSTEMS"

    # Network equipment
    network_equipment: Optional[str] = Field(None, description="Network equipment involved (routers, APs, etc.)")
    switches_involved: Optional[str] = Field(None, description="Switch models and ports affected")
    ip_addresses: Optional[str] = Field(None, description="IP addresses configured or affected")

    # Cabling
    cable_work: Optional[str] = Field(None, description="Description of cable work (Cat6, fibre, etc.)")
    cable_length_m: Optional[float] = Field(None, description="Total cable length installed in metres")
    fibre_type: Optional[str] = Field(None, description="Fibre optic type (OS2, OM3, etc.)")
    patch_panels: Optional[str] = Field(None, description="Patch panel port assignments")

    # Security
    cameras: Optional[str] = Field(None, description="Cameras installed, configured, or replaced")
    camera_ip: Optional[str] = Field(None, description="Camera IP address(es)")
    access_control: Optional[str] = Field(None, description="Access control hardware/software changes")

    # Software / systems
    software_changes: Optional[str] = Field(None, description="Software changes, updates, or installations")
    backup_performed: Optional[bool] = Field(None, description="Was a data backup performed?")
    system_tested: Optional[bool] = Field(None, description="Was the system tested after work?")
    test_result: Optional[str] = Field(None, description="System test results / verification")


class ElectricalFields(BaseModel):
    """Fields for Electrical Engineering department work."""
    dept_schema_type: str = "ELECTRICAL"

    # Circuit identification
    panel_reference: Optional[str] = Field(None, description="Panel / MCC reference (e.g. MCC-01)")
    circuit_number: Optional[str] = Field(None, description="Circuit or breaker number")
    voltage_level: Optional[str] = Field(None, description="Voltage level (e.g. 415V, 11kV, 24VDC)")

    # Cable & conductors
    cable_size: Optional[str] = Field(None, description="Cable size and type (e.g. 25mm² Cu XLPE)")
    cable_length_m: Optional[float] = Field(None, description="Cable length installed in metres")

    # Protection
    protection_settings: Optional[str] = Field(None, description="Protection relay settings applied")
    relay_settings: Optional[str] = Field(None, description="Relay model and configured settings")
    fuse_rating: Optional[str] = Field(None, description="Fuse rating installed (e.g. 32A HRC)")

    # Testing
    insulation_resistance: Optional[str] = Field(None, description="Insulation resistance test results (MΩ)")
    earth_continuity: Optional[str] = Field(None, description="Earth continuity test readings")
    continuity_test: Optional[bool] = Field(None, description="Continuity test passed?")
    loop_test: Optional[bool] = Field(None, description="Loop test passed?")


class CivilFields(BaseModel):
    """Fields for Civil Engineering / Construction department work."""
    dept_schema_type: str = "CIVIL"

    structure_type: Optional[str] = Field(None, description="Structure type (e.g. concrete slab, retaining wall)")
    concrete_grade: Optional[str] = Field(None, description="Concrete grade specified / used")
    steel_grade: Optional[str] = Field(None, description="Steel grade (rebar, structural)")
    dimensions: Optional[str] = Field(None, description="Key dimensions of structure/repair (L x W x D)")
    surface_prep: Optional[str] = Field(None, description="Surface preparation method")
    curing_time: Optional[str] = Field(None, description="Curing time or drying time specified")


class HSEFields(BaseModel):
    """Fields for Health, Safety & Environment department work."""
    dept_schema_type: str = "HSE"

    hazard_identified: Optional[str] = Field(None, description="Hazards identified before work started")
    controls_applied: Optional[str] = Field(None, description="Control measures implemented")
    ppe_required: Optional[str] = Field(None, description="PPE required for the task")
    permits_issued: Optional[str] = Field(None, description="Permits issued (hot work, confined space, etc.)")
    incident_occurred: Optional[bool] = Field(None, description="Was an incident recorded during work?")
    incident_reference: Optional[str] = Field(None, description="Incident reference number if applicable")
    environmental_impact: Optional[str] = Field(None, description="Environmental impact or spill details")


class GenericFields(BaseModel):
    """Catch-all for departments without a specific schema."""
    dept_schema_type: str = "GENERIC"
    notes: Optional[str] = Field(None, description="Any department-specific notes")
    custom_data: Optional[dict] = Field(None, description="Any additional key-value data")


# ── Type mapping ──────────────────────────────────────────────

_SCHEMA_MAP: dict[str, type[BaseModel]] = {
    "MECHANICAL": MechanicalFields,
    "INSTRUMENTATION": InstrumentationFields,
    "IT_SYSTEMS": ITSystemsFields,
    "ELECTRICAL": ElectricalFields,
    "CIVIL": CivilFields,
    "HSE": HSEFields,
    "STORES": GenericFields,
    "GENERIC": GenericFields,
}

DeptSchemaType = str  # One of DEPT_SCHEMA_TYPES from report_models.py


def validate_dept_data(dept_schema_type: str, data: dict | None) -> dict | None:
    """
    Validate dept_specific_data against the appropriate department sub-schema.
    Returns a cleaned dict, or None if data is None/empty.
    Raises ValidationError if the data doesn't conform to the schema.
    """
    if not data:
        return None
    schema_cls = _SCHEMA_MAP.get(dept_schema_type, GenericFields)
    validated = schema_cls.model_validate(data)
    return validated.model_dump(exclude_none=True)


def get_dept_schema_fields(dept_schema_type: str) -> list[dict[str, Any]]:
    """
    Return a list of field metadata dicts for the given dept type.
    Used by the frontend to dynamically render the correct form fields.
    """
    schema_cls = _SCHEMA_MAP.get(dept_schema_type, GenericFields)
    fields = []
    for field_name, field_info in schema_cls.model_fields.items():
        if field_name == "dept_schema_type":
            continue
        fields.append({
            "name": field_name,
            "label": field_name.replace("_", " ").title(),
            "description": field_info.description or "",
            "type": str(field_info.annotation),
        })
    return fields
