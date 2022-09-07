import os
from ruamel.yaml import YAML, RoundTripDumper

yaml = YAML(typ="rt")  # default, if not specfied, is 'rt' (round-trip)


def get_yaml_from_frontmatter(file):
    """
    jekyll front matter puts yaml content between a first line of '---' and closes with a line of '---'.
    Read in all the file as a string. Extract the yaml string from between the two '---' and load that.
    """
    with open(file, "r") as stream:
        data = stream.read()
    yaml_string = data.split("---")[1]
    return yaml.load(yaml_string)


def put_yaml_with_frontmatter(file, data):
    """
    Function that puts the YAML data into a YAML file with a front matter.
    This is prepended with a line of '---' and post-pended with a line of '---'.
    """
    with open(file, "w") as stream:
        stream.write("---\n")
        yaml.dump(data, stream)
        stream.write("---\n")


def remove_countries(file_name):
    """
    Function that removes all countries from the 'categories' item in the YAML file
    """
    print("Removing countries from " + file_name)
    data = get_yaml_from_frontmatter(file_name)
    for category in data["category"]:
        print(category)
        if category not in ["People", "Groups & Bodies"]:
            data["category"].remove(category)
    put_yaml_with_frontmatter(file_name, data)


def main():
    """
    Main function that iterates through every YAML file in the _datasets folder and calls the
    remove_countries function
    """
    for file in os.listdir("_datasets"):
        if file.startswith("everypolitician-"):
            remove_countries("_datasets/" + file)


if __name__ == "__main__":
    main()
    print("Done")
