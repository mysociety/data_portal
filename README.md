# mySociety Data Portal repo - running on JKAN

A lightweight, backend-free open data portal, powered by Jekyll

View at data.mysociety.org


## Updating from datapackages repos

* Add the new page to the `datapackages.yaml` file. The github action should sync relevant content from that. 

## Local Development

There is a docker config that will work locally or on codespaces. 

Within this `script/server` will run the local debug server.

This will then start the rendering process and serve on http://127.0.0.1:4000

## Theme

Jkan runs on Jekyll.

Local adaptions to mySociety theme are in sass folder - both that and 'theme/sass' are equally accessible to compiler - so no need for relative paths. 

Key template is templates/default.html - this then brings in various mysoc_ includes. 

Don't forget to `git submodule update --init --recursive` to pull down the mySociety styles


## Categories

Category information is stored in three places. 
 
1. References in datasets
2. Entries in _data/categories.yml (with additional info like logos, or if they are a highlighted category)
3. Markdown files in /_categories

The final set is generated from the first two to create the static pages for the category pages. 

Category pages are generated by:

    $ ruby script/generate_categories.rb

A Github Action will take care of this.

