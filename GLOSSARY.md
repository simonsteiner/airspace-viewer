# Airspace Viewer

Views airspace definitions written in the OpenAir format on a map, so pilots and competition organizers can check what a file contains.

## Language

### Files

**OpenAir file**:
A text file describing airspaces in the OpenAir format, one record per airspace.
_Avoid_: airspace file, air file

**Example file**:
An OpenAir file that ships with the app and can be picked from its menu.
_Avoid_: sample, demo file

**Default file**:
The example file loaded at startup and restored by reset (Switzerland).
_Avoid_: base file

**Active dataset**:
The airspaces currently shown on the map, from the last file loaded; there is one for everyone using the app.
_Avoid_: current file, session data

### Airspaces

**Airspace**:
One volume of sky from an OpenAir file: a name, a class, a type, lower and upper bounds, and a horizontal outline.
_Avoid_: zone, area, region

**Class token**:
The raw value of an airspace's `AC` line, such as `R`, `Q`, `CTR` or `UNC`.
_Avoid_: AC code, class code

**Type token**:
The raw value of an airspace's `AY` line in OpenAir v2, naming the kind of area when the class token is `UNC`.
_Avoid_: kind, category

**Legacy class token**:
A class token from before OpenAir v2 that names a kind of area rather than an ICAO class, such as `R` for restricted or `Q` for danger.
_Avoid_: old class

**Display class**:
The class an airspace is shown as: its color, legend entry and label, such as `Restricted` for the class token `R`.
_Avoid_: airspace type, category, color class

**Bound**:
The lower or upper limit of an airspace, as an altitude above sea level or ground, a flight level, the ground itself or unlimited.
_Avoid_: floor, ceiling, limit

### Output

**KML export**:
The active dataset as a KML file for Google Earth and similar tools.
_Avoid_: download, KML dump
