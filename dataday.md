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

### No Data Day in 2020

**The UCDS will not organize a 2020 Data Science Day.**  Due to the pandemic, unsafeness of large gatherings, and lack of a worthy online alternative, we have decided not to pursue a Data Science Day this year.  We look forward for future opportunities to run in person (or suitable virtual) events in the near future.    

---

### Past Highlights
{% include image_gallary.html %}

---

### Past Data Science Days
{% assign events = site.pages | where:"categories","dataday" |sort: "date" | reverse %}
{% for eventpage in events %}
* [{{ eventpage.title }}]({{ eventpage.url }})
{% endfor %}
