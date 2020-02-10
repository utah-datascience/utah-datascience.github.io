---
layout: single
title: Members
excerpt: >
  Description. Description. Description. Description. Description.
  Description. Description. Description. Description. Description.
---


<h3 class="display-3 text-center mb-3">Core Members</h3>

{% assign members_list = site.members | where: "type", "core"  | sort: 'date' %}
{% include members_list.html members_list = members_list %}

<h3 class="display-3 text-center mb-3">Affiliated Members</h3>
{% assign members_list = site.members | where: "type", "affiliated"  | sort: 'date' %}
{% include members_list.html members_list = members_list %}