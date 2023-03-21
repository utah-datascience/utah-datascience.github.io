---
layout: single
title: Programs
header:
  title: Academic Programs
  excerpt: >
    Data Science education takes many forms. We list many of the associated programs at the Univesity of Utah.
  background-image: /assets/img/header-background/zion-shorter.jpg
---

{% assign programs = site.programs | sort: 'name' %}
{% for program in programs %}
<div class="row justify-content-center pb-4">
  <div class="col-lg-12">
    <h3>{{ program.name }}</h3>
    {{ program.content | markdownify }}
    <a href="{{ program.link }}" target="_blank" rel="noopener noreferrer">Show more</a>
  </div>
</div>
{% endfor %}

<div class="pt-4 border-top text-center">
  <div class="row justify-content-center">
    <div class="col-lg-9">
      <p><I>Disclaimer:</I> This page is under construction. If you find a Utah course or program that we have
      not listed here, please contact us at the email address below and we will include it here.</p>
    </div>
  </div>
</div>
