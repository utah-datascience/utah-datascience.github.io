---
layout: single
title: Members
excerpt: >
  The UCDS is led by a director, with the assistance of associate directors and the other core members.  The Associate Direct or Research organizes research-focused events like the <a href="seminar.html">Data Science Seminar</a>.  The Associare Director of Outreach builds relations with other researchers around campus, including through the annual <a href="dataday.html">Data Science Day</a>.  And the Associate Director of Student Involvement leads efforts to engage students in data science, including as liason to associated <a href="club.html">student groups</a>.  
  The Affiliated members repsents the centers connections around campus into the many disciplines where data science reaches.  
---
<p class="lead  text-black secondary-ex">
  {{ page.excerpt | markdownify | remove: "<p>" | remove: "</p>" }}
  <br>
  <br>
 </p>

<h3 class="display-3 text-center mb-3">Core Members</h3>

{% assign members_list = site.members | where: "type", "core"  | sort: 'date' %}
{% include members_list.html members_list = members_list %}

<h3 class="display-3 text-center mb-3">Affiliated Members</h3>
{% assign members_list = site.members | where: "type", "affiliated"  | sort: 'date' %}
{% include members_list.html members_list = members_list %}
