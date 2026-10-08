import requests
import os
import json

def get_building_coords():
  url = (
      "https://gismaps.unc.edu/arcgis/rest/services/"
      "UNCOpenData/UNCOpenData/MapServer/2/query"
  )

  params = {
      "where": "1=1",
      "outFields": "BUILDINGNUMBER,BUILDINGNAME,BUILDINGADDRESS",
      "returnGeometry": "true",
      "outSR": "4326",  # convert to latitude/longitude
      "f": "geojson",
  }

  response = requests.get(url, params=params)
  response.raise_for_status()

  data = response.json()

  facilities = []

  for feature in data["features"]:
      properties = feature["properties"]
      longitude, latitude = feature["geometry"]["coordinates"]

      facilities.append({
          "facility_id": properties["BUILDINGNUMBER"],
          "name": properties["BUILDINGNAME"],
          "address": properties["BUILDINGADDRESS"],
          "latitude": latitude,
          "longitude": longitude,
      })

  return facilities

def save_building_coords(output_directory="scraped_data"):
    building_data_path = os.path.join(output_directory, "building_coords.json")
    building_data = get_building_coords()

    with open(building_data_path, "w", encoding="utf-8") as file:
        json.dump(building_data, file, indent=2)

if __name__ == "__main__":
  save_building_coords()