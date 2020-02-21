---
layout: single
title: Members
header:
  title: Members
  background-image: /assets/img/header-background/zion-shorter.jpg
---


## Leadership

{% assign members_list = site.members | where: "type", "leadership"  | sort: 'key' %}
{% include members_list.html members_list = members_list %}

## Core Members

{% assign members_list = site.members | where: "type", "core"  | sort: 'key' %}
{% include members_list.html members_list = members_list %}

## Affiliated Members
{% assign members_list = site.members | where: "type", "affiliated"  | sort: 'key' %}
{% include members_list.html members_list = members_list %}

---

### Organization and By-Laws

The UCDS is led by a director, with the assistance of associate directors and the other core members.  The Associate Direct or Research organizes research-focused events like the <a href="seminar.html">Data Science Seminar</a>.  The Associate Director of Outreach builds relations with other researchers around campus, including through the annual <a href="dataday.html">Data Science Day</a>.  And the Associate Director of Student Involvement leads efforts to engage students in data science, including as liason to associated <a href="club.html">student groups</a>. The Affiliated members represents the centers connections around campus into the many disciplines where data science reaches.


[Governance Roles](./assets/file/UCDS-Elections[7996].pdf)

[Membership Plans](./assets/file/UCDS-Affiliate[7995].pdf)
