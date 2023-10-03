from __future__ import print_function
import csv
import subprocess
import re
import os
import numpy as np

SAMPLES = 3601
HGTDIR = 'hgt'
HGTFILENAME = 'N43W081.hgt'

def get_elevation(lat, lon):
    hgt_file = os.path.join(HGTDIR, HGTFILENAME)
    if hgt_file:
        return read_elevation_from_file(hgt_file, lat, lon)
    return -32768

def read_elevation_from_file(hgt_file, lat, lon):
    with open(hgt_file, 'rb') as hgt_data:
        elevations = np.fromfile(
            hgt_data,
            np.dtype('>i2'),
            SAMPLES * SAMPLES
        ).reshape((SAMPLES, SAMPLES))

        lat_row = int(round((lat - int(lat)) * (SAMPLES - 1), 0))
        lon_row = int(round((lon - int(lon)) * (SAMPLES - 1), 0))

        return elevations[SAMPLES - 1 - lat_row, lon_row].astype(int)


input_csv_file = open("Three_Amigos_day_1.csv", "r", encoding='utf-8-sig')
input_csv = csv.DictReader(input_csv_file)
updated_csv = []

headers = input_csv.fieldnames

def get_elevation_from_gdallocationinfo(filename, lat, lon):
    output = subprocess.check_output([
        'gdallocationinfo', filename, '-wgs84', str(lon), str(lat)
    ])
    return int(re.search('Value: (\d+)', str(output)).group(1))


count = 0
previous_altitude = 0
for row in input_csv:
    updated_row = row.copy()
    if updated_row["Type"] == "Data":
        if updated_row["Field 2"] == "position_lat" and updated_row["Field 3"] == "position_long" and updated_row["Field 5"] == "altitude" and updated_row["Field 12"] == "enhanced_altitude" and updated_row["Field 14"] == "ascent" and updated_row["Field 15"] == "descent":
            decimal_lat = int(row["Value 2"]) / 11930465 
            decimal_long = int(row["Value 3"]) / 11930465
            altitude = float(row["Value 5"])
            print(f'Latitude: {decimal_lat}, Longitude: {decimal_long}, Altitude: {altitude}')
            fixed_altitude = get_elevation(decimal_lat, decimal_long)
            print(f'Fixed altitude {fixed_altitude}')
            updated_row["Value 5"] = fixed_altitude
            updated_row["Value 12"] = fixed_altitude
            elevation_diff = fixed_altitude - previous_altitude
            if elevation_diff > 0:
                updated_row["Value 14"] = elevation_diff
            else:
                updated_row["Value 15"] = elevation_diff
            previous_altitude = fixed_altitude
            count += 1
            print(f'Parsed {count} entries')
    updated_csv.append(updated_row)

input_csv_file.close()
output_csv_file = open('three_amigos_day_1_fixed_altitude.csv', "w", newline="", encoding='utf-8-sig')
output_data = csv.DictWriter(output_csv_file, delimiter=',', fieldnames=headers)
output_data.writerow(dict((heads, heads) for heads in headers))
output_data.writerows(updated_csv)
output_csv_file.close()
