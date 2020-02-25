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

### Highlights
<style>
div.gallery {
  margin: 5px;
  float: left;
  width: 230px;
  height: 153px;
}
</style>
<div>
{% for image in site.static_files %}
  {% if image.path contains "2019highlights" %}
  <div class="gallery">
  <img src="{{ image.path }}" alt="2019 dataday highlith" width="100%" />
  </div>
  {% endif %}
{% endfor %}
</div>

---

### Past Data Science Days
{% assign events = site.pages | where:"categories","dataday" |sort: "date" | reverse %}
{% for eventpage in events %}
* [{{ eventpage.title }}]({{ eventpage.url }})
{% endfor %}
