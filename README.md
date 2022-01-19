# Utah Data Science Center

Original theme: https://jamstack-argon-design.appseed.us/index.html

## Local run
* For the first time, install [jekyll](https://jekyllrb.com/docs/installation/), if windows, you may need further run `bundle add webrick`.
Then run
```shell
bundle install
```
* If failed because of gem version incompatible, try
```shell
bundle update
```
This will update `Gemfile.lock`.
* To serve the website locally, run
```shell
bundle exec jekyll serve
```

## Content Edit

### Members
Add/delete/edit .md files in `_members` directory to add/delete/edit members. 

`Director, Associate Director of Research, ...` are called *roles*, order and available values for role are hard coded in `members.md` file.

Members in the same role are sorted by the file name. Please name them in the format like `Lastname-Firstname-Middlename.md`. Here is an example file content:

```YAML
---
name: Jeff M. Phillips
role: Director
title: |
    Associate Professor, School of Computing, University of Utah
link: http://www.cs.utah.edu/~jeffp/
pic: assets/img/member_photos/jeff.png
---
He specializes in designing algorithms for data science.
```

The available variables are:

| Variable | Description |
| -------- | ------------- |
| name     | The name of the member to be shown.    |
| role     | Under which role to diplay the member. Available values are hard coded in `members.md` file.|
| title    | Title of the member to be display under the name. Using block style indicator `|` to keep newlines between multiline. |
| link     | The link for the photo and name. |
| pic      | The photo of the member. It can be an exist link to an image, or a path to the image. |

> **_NOTE:_**  The subfolders (affiliated, core, and leadership) under `_members` have no effects. They exist only for organizing these files. To show member under a role, set the role variable in its .md file with a right value.

### progrmas
Add/delete/edit .md files in `_progrmas` folder to add/delete/edit members.

## Page header
* header:
  * title: Header Title, default: None
  * title-color: white|red, default: white
  * excerpt: >  
        Excerpt to show under title, default: None
  * excerpt-color: white|black, default: white
  * align: center|left, default: center
  * background-image: default: /assets/img/header-background/zion-shorter.jpg

## Layout
* home
  Designed for landing page, does not defined a content box.
* single
  Designed for content page, predefined a content box to include all content in a white backgound card.
  
## Scheduling Website Changes

You can schedule a website change to occur at 00:01 any day by doing the following:

1. Create a branch where you will make your changes.
2. On your branch, make your changes and test them.
3. Once you’re ready, you need to submit a Pull Request. At the very bottom of your Pull Request description, add `/schedule yyyy-mm-dd`. Your change will be merged to master at ~12:01 am on this date.

This scheduler is implemented using the Merge Schedule GitHub Action. More information on this can be found [here](https://github.com/marketplace/actions/merge-schedule).