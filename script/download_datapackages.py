"""
Download information from data packages and create entries in the _datasets folder.
"""
from pathlib import Path
from ruamel.yaml import YAML, RoundTripDumper
from bs4 import BeautifulSoup
from typing import Any
from urllib.request import urlopen
import json

yaml=YAML(typ='rt')   # default, if not specfied, is 'rt' (round-trip)


def put_yaml_with_frontmatter(file: Path, data: dict[str: Any]):
    """
    Function that puts the YAML data into a YAML file with a front matter.
    This is prepended with a line of '---' and post-pended with a line of '---'.
    """
    with open(file, 'w') as stream:
        stream.write('---\n')
        yaml.dump(data, stream)
        stream.write('---\n')
    print(f"Wrote {file}")

def get_yaml_from_frontmatter(file: Path) -> dict[str, Any]:
    """
    jekyll front matter puts yaml content between a first line of '---' and closes with a line of '---'.
    Read in all the file as a string. Extract the yaml string from between the two '---' and load that.
    """
    with open(file, 'r') as stream:
        data = stream.read()
    yaml_string = data.split('---')[1]
    return yaml.load(yaml_string)


def get_datapackages() -> dict[str, list[str]]:
    """
    Opens up the `datapacakges.yaml` file one level up.
    This is a dict of domains to a list of subfolder with a datapackage site.
    """
    with open('datapackages.yaml', 'r') as stream:
        data = stream.read()
    return yaml.load(data)


def process_all_datapackages():
    data = get_datapackages()
    for domain, list_of_folders in data.items():
        for datapackage in list_of_folders:
            process_datapackage_repo(domain, datapackage)



def process_datapackage_repo(domain:str, datapackage: str):
    print('Processing ' + domain + ' ' + datapackage)
    url = f"https://{domain}/{datapackage}"
    data_packages = get_datapackages_from_front_page(url)
    for d in data_packages:
        create_yaml_from_datapackage(domain, datapackage, d)


def get_datapackages_from_front_page(url: str) -> list[str]:
    """
    Get the list of datapackages from the front page of the site.
    """
    # get content of url into soup
    soup = BeautifulSoup(urlopen(url), 'html.parser')
    # get unordered list underneath a h2 that says 'Datasets'
    ul = soup.find('h2', text='Datasets').find_next('ul')
    # iterate through the items and get the link of the URL in the content of the li.
    links = [li.find('a')['href'] for li in ul.find_all('li')]
    # extract the datapackage name from the link. This is in the format url/datapackage_name/latest.
    return [l.split('/')[-2] for l in links]

def create_yaml_from_datapackage(domain: str, subfolder: str, package: str) -> None:

    dest_filename = Path(f"_datasets/{subfolder}_{package}.md")
    if dest_filename.exists():
        yaml_data = get_yaml_from_frontmatter(dest_filename)
        print(f"{dest_filename} already exists. Updating.")
    else:   
        yaml_data = {"schema": "default"}
    page_url = f"https://{domain}/{subfolder}/datasets/{package}/latest"
    data_package_url = f"https://{domain}/{subfolder}/data/{package}/latest/datapackage.json"
    # download and load json into a dict
    with urlopen(data_package_url) as stream:
        data = json.load(stream)
    yaml_data["title"] = data["title"]
    yaml_data["notes"] = data["description"]
    yaml_data["more_info"] = page_url
    yaml_data["resources"] = []
    for resource in data["resources"]:
        yaml_data["resources"].append({"name": resource["title"], "url": page_url, "format":"info"})

    keywords = data.get("keywords", []) + yaml_data.get("yaml_data", [])
    keywords.sort()
    yaml_data["category"] = keywords

    put_yaml_with_frontmatter(dest_filename, yaml_data)


if __name__ == '__main__':
    process_all_datapackages()
    print('Done')