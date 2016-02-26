from setuptools import setup, find_packages

installRequires = []
dependencyLinks = []

with open("requirements.txt", "r") as reqfile:
  for line in reqfile:
    installRequires.append(line.strip())

setup(
  name = "smartthings_htm_bridge",
  description = "SmartThings HTM Bridge saves IOT sensor data into InfluxDB "
                "and makes it easier to process with HTM.",
  packages = find_packages(),
  include_package_data=True,
  install_requires = installRequires,
  entry_points = {
    "console_scripts": [
      "st_htm_bridge_cli = st_htm_bridge.cli:main"
    ]
  }
)
