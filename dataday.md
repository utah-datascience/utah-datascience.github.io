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

### Data Science Day 2022

The UCDS is planning to host an in-person Data Science Day on January 14, 2022 at the Union Ball Room (if the pandemic cooperates).  Contact datasci@utah.edu if you are interested to participate.  More details forthcoming. 

---

### Past Highlights
{% include image_gallary.html %}

---

### Past Data Science Days
{% assign events = site.pages | where:"categories","dataday" |sort: "date" | reverse %}
{% for eventpage in events %}
* [{{ eventpage.title }}]({{ eventpage.url }})
{% endfor %}
