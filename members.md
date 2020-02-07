---
layout: single
title: Members
excerpt: >
  Description. Description. Description. Description. Description.
  Description. Description. Description. Description. Description.
---

{% assign members = site.members | sort: 'date' %}
{% for member in members %}
<div class="row justify-content-center pb-4">
  <div class="col-lg-12 d-flex">
    <div class="col-lg-3">
      <img src="{{ '/assets/img/members/' | relative_url }}{{ member.pic }}" alt="Picture of {{ member.name }}" class="img-fluid rounded shadow" style="width: 200px;">
    </div>
    <div class="col-lg-9">
      <h4><a href="{{ member.link }}" class="btn-link text-primary">{{ member.name }}</a></h4>
      <h6>{{ member.title }}</h6>
      <span class="description">{{ member.content | markdownify }}</span>
    </div>
  </div>
</div>
{% endfor %}
