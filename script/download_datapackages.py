"""
Download information from data packages and create entries in the _datasets folder.
"""

from pathlib import Path
from ruamel.yaml import YAML, RoundTripDumper
from bs4 import BeautifulSoup
from typing import Any
from urllib.request import urlopen
import json
import duckdb

yaml = YAML(typ="rt")  # default, if not specfied, is 'rt' (round-trip)


def put_yaml_with_frontmatter(file: Path, data: dict[str:Any]):
    """
    Function that puts the YAML data into a YAML file with a front matter.
    This is prepended with a line of '---' and post-pended with a line of '---'.
    """
    with open(file, "w") as stream:
        stream.write("---\n")
        yaml.dump(data, stream)
        stream.write("---\n")
    print(f"Wrote {file}")


def get_yaml_from_frontmatter(file: Path) -> dict[str, Any]:
    """
    jekyll front matter puts yaml content between a first line of '---' and closes with a line of '---'.
    Read in all the file as a string. Extract the yaml string from between the two '---' and load that.
    """
    with open(file, "r") as stream:
        data = stream.read()
    yaml_string = data.split("---")[1]
    return yaml.load(yaml_string)


def get_datapackages() -> dict[str, list[str]]:
    """
    Opens up the `datapacakges.yaml` file one level up.
    This is a dict of domains to a list of subfolder with a datapackage site.
    """
    with open(Path("_data", "datapackages.yaml"), "r") as stream:
        data = stream.read()
    return yaml.load(data)


def process_all_datapackages():
    data = get_datapackages()
    for domain, list_of_folders in data["domains"].items():
        for datapackage in list_of_folders:
            process_datapackage_repo(domain, datapackage)


def process_datapackage_repo(domain: str, datapackage: str):
    print("Processing " + domain + " " + datapackage)
    url = f"https://{domain}/{datapackage}"
    data_packages = get_datapackages_from_front_page(url)
    for d in data_packages:
        create_yaml_from_datapackage(domain, datapackage, d)


def get_datapackages_from_front_page(url: str) -> list[str]:
    """
    Get the list of datapackages from the front page of the site.
    """
    # get content of url into soup
    soup = BeautifulSoup(urlopen(url), "html.parser")
    # get unordered list underneath a h2 that says 'Datasets'
    ul = soup.find("h2", string="Datasets").find_next("ul")
    # iterate through the items and get the link of the URL in the content of the li.
    links = [li.find("a")["href"] for li in ul.find_all("li")]
    # extract the datapackage name from the link. This is in the format url/datapackage_name/latest.
    return [l.split("/")[-2] for l in links]


keyword_correct = {
    "UK Local data": "UK Local Authority data",
    "LSOA": "Small Area (LSOA) data",
}


def create_yaml_from_datapackage(domain: str, subfolder: str, package: str) -> None:
    dest_filename = Path(f"_datasets/{subfolder}_{package}.md")
    if dest_filename.exists():
        yaml_data = get_yaml_from_frontmatter(dest_filename)
        print(f"{dest_filename} already exists. Updating.")
    else:
        yaml_data = {"schema": "default"}
    page_url = f"https://{domain}/{subfolder}/datasets/{package}/latest"
    data_package_url = (
        f"https://{domain}/{subfolder}/data/{package}/latest/datapackage.json"
    )
    # download and load json into a dict
    with urlopen(data_package_url) as stream:
        data = json.load(stream)
    yaml_data["title"] = data["title"]
    yaml_data["notes"] = data["description"]
    yaml_data["more_info"] = page_url
    yaml_data["resources"] = []
    for resource in data["resources"]:
        yaml_data["resources"].append(
            {"name": resource["title"], "url": page_url, "format": "info"}
        )

    keywords = data.get("keywords", []) + yaml_data.get("category", [])
    keywords = [keyword_correct.get(k, k) for k in keywords]
    # make keywords unique and sorted
    yaml_data["category"] = sorted(list(set(keywords)))

    put_yaml_with_frontmatter(dest_filename, yaml_data)




def slugify(s: str) -> str:
    # lower case, hythens, dots and spaces are underscores
    s = s.lower().replace("-", "_").replace(" ", "_").replace(".", "_")
    # remove all non-alphanumeric characters except underscores
    s = "".join([c for c in s if c.isalnum() or c == "_"])
    return s


def make_duck_db():


    schemas: dict[str, dict[str, str]] = {}
    banned_no_parquets = ["scotland-climate-projects-data"]

    data = get_datapackages()
    for domain, list_of_folders in data["domains"].items():
        for data_repo in list_of_folders:
            if data_repo in banned_no_parquets:
                continue
            url = f"https://{domain}/{data_repo}"
            data_packages = get_datapackages_from_front_page(url)
            for package in data_packages:
                resource_links = {}
                data_package_url = f"https://{domain}/{data_repo}/data/{package}/latest/datapackage.json"
                data = json.load(urlopen(data_package_url))
                resources = {x["name"]: x["path"] for x in data["resources"]}
                for name, csv in resources.items():
                    csv_file = Path(csv).stem
                    parquet_url = f"https://{domain}/{data_repo}/data/{package}/latest/{csv_file}.parquet"
                    resource_links[slugify(name)] = parquet_url
                schemas[slugify(package)] = resource_links

    commands = []
    for schema, data in schemas.items():
        commands.append(f"CREATE SCHEMA {schema};")
        for resource, url in data.items():
            commands.append(f"CREATE VIEW {schema}.{resource} as SELECT * FROM '{url}';")

    duckdb_database = Path("duck", "mysoc.db")
    # ensure parent directory exists
    duckdb_database.parent.mkdir(parents=True, exist_ok=True)
    if duckdb_database.exists():
        duckdb_database.unlink()
    con = duckdb.connect(str(duckdb_database))
    for command in commands:
        con.execute(command)
    con.close()

    


if __name__ == "__main__":
    process_all_datapackages()
    make_duck_db()
    # data = get_datapackages()
    # for domain, list_of_folders in data["domains"].items():
    # print("Done")
