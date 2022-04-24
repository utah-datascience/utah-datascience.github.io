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

The 2022 Data Science Day has been canceled due to the pandemic.

---

### Past Highlights
{% include image_gallary.html folder="assets/img/dataday/2019highlights"%}

---

### Past Data Science Days
{% assign events = site.pages | where:"categories","dataday" |sort: "date" | reverse %}
{% for eventpage in events %}
* [{{ eventpage.title }}]({{ eventpage.url }})
{% endfor %}
