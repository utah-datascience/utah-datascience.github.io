---
layout: single
title: Events
header:
  title: Data Science Day
  excerpt: >
    The UCDS organizes and annual Data Science Day on the campus of the University of Utah.
    This event brings together resarchers and students from across campus and the community, and local industry.
    Its an ideal setting to learn or share recent research ... or for industry to recruit our most enganged students.
  background-image: /assets/img/header-background/zion-shorter.jpg
---

#### Past Data Science Days
{% assign events = site.pages | where:"categories","dataday" %}
{% for eventpage in events %}
* [{{ eventpage.title }}]({{ eventpage.url }})
{% endfor %}
