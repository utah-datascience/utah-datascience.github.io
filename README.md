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

### progrmas
Add/delete/edit .md files in `_progrmas` folder to add/delete/edit members.

## Page header
* header:
  * title: Header Title, default: Utah Center for Data Science
  * title-color: white|red, default: white
  * excerpt: >
        Excerpt/Discription of this page.
        default: None
  * excerpt-color: white|black, default: white
  * align: center|left, default: center
  * background-image: default: /assets/img/header-background/lauren-pandolfi-zD5ry8Up83M-unsplash.jpg

## Layout
* home
  Designed for landing page, does not defined a content box.
* single
  Designed for content page, predefined a content box to include all content in a white backgound card.