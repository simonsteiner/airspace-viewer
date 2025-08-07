from openair import parse_file

from app.model.openair_types import convert_raw_airspace
from app.utils.kml_converter import convert_airspace_to_kml

# Use a real OpenAir file
example_file = "app/examples/Airspace-Disentis-2025-MIL-OFF-min-2.txt"

# Parse the OpenAir file to get raw airspace dicts
raw_airspaces = parse_file(example_file)

# Convert raw dicts to Airspace objects
airspace_objs = [convert_raw_airspace(raw) for raw in raw_airspaces]

# Convert to KML
kml_str = convert_airspace_to_kml(airspace_objs)
print(kml_str)
