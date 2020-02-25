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

{%comment%}
### Highlights
<div style="display: flex; flex-flow: row wrap;">
  {% for image in site.static_files %}
    {% if image.path contains "2019highlights" %}
      <img src="{{ image.path }}" alt="2019 dataday highlith" width="40%" style="flex: 50%;"/>
    {% endif %}
  {% endfor %}
</div>
{%endcomment%}

#### Past Data Science Days
{% assign events = site.pages | where:"categories","dataday" |sort: "date" | reverse %}
{% for eventpage in events %}
* [{{ eventpage.title }}]({{ eventpage.url }})
{% endfor %}
