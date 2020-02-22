# Utah Data Science Center

Original theme: https://jamstack-argon-design.appseed.us/index.html

## Local run
For the first time, after installing ruby-dev, install jekyll:
```shell
gem install jekyll bundler
bundle install
```
To serve the website locally, run
```shell
bundle exec jekyll serve
```

## Content Edit

### Members
Add/delete/edit .md files in `_members` folder to add/delete/edit members.

Members in the same role are sorted by the file name. Please name them in format `Lastname-Firstname-Middlename.md`. Here is an example file content:

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
| role     | Under which role to diplay the member. |
| title    | Title of the member to be display under the name. Using block style indicator `|` to keep newlines between multiline. |
| link     | The link for the photo and name. |
| pic      | The photo of the member. |

> **_NOTE:_**  The subfolders (affiliated, core, and leadership) under `_members` is meaningless, they exist only for convenient maintaining. To show member under a role, the role variable in the YAML _front matter_ block has to be signed with a right role.

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
  * background-image: default: /assets/img/header-background/lauren-pandolfi-midium.jpg

## Layout
* home
  Designed for landing page, does not defined a content box.
* single
  Designed for content page, predefined a content box to include all content in a white backgound card.