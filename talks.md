---
layout: single
title: Talks
permalink: /talks/
header:
  title: Talks
  excerpt: |
    Every talk in the Data Science &amp; AI Lecture Series, with abstracts, speaker bios, slides, and recordings.

    [Lecture Series](/seminar.html)
    {: class="btn btn-neutral"}
  background-image: /assets/img/header-background/zion-shorter.jpg
---

{%- assign now = site.time | date: "%s" | plus: 0 -%}
{%- assign all_talks = site.talks | sort: "date" -%}
{%- assign upcoming = "" | split: "" -%}
{%- assign past = "" | split: "" -%}
{%- for talk in all_talks -%}
  {%- assign talk_time = talk.date | date: "%s" | plus: 0 -%}
  {%- if talk_time >= now -%}
    {%- assign upcoming = upcoming | push: talk -%}
  {%- else -%}
    {%- assign past = past | push: talk -%}
  {%- endif -%}
{%- endfor -%}
{%- assign past = past | reverse -%}

<style>
  ul.talk-list { list-style: none; padding-left: 0; }
  ul.talk-list li { margin-bottom: 1rem; }
  ul.talk-list .talk-date { display: inline-block; min-width: 8.5rem; }
</style>

## Upcoming

{% if upcoming.size > 0 %}
<ul class="talk-list">
  {% for talk in upcoming %}
  <li>
    <span class="talk-date text-muted">{{ talk.date | date: "%b %-d, %Y" }}</span>
    <a href="{{ talk.url | relative_url }}">{{ talk.title }}</a>
    &mdash; {{ talk.speaker_names }}
    {% if talk.canceled %}<span class="badge badge-danger">Canceled</span>{% endif %}
  </li>
  {% endfor %}
</ul>
{% else %}
<p>No talks scheduled right now. Check back soon, or
<a href="https://mailman.cs.utah.edu/mailman3/lists/ucds-seminar.cs.utah.edu/">join the mailing list</a>.</p>
{% endif %}

## Past talks

{% assign current_year = "" %}
{% for talk in past %}
  {%- assign year = talk.date | date: "%Y" -%}
  {% if year != current_year %}
    {% unless forloop.first %}</ul>{% endunless %}
<h3 id="y{{ year }}">{{ year }}</h3>
<ul class="talk-list">
    {% assign current_year = year %}
  {% endif %}
  <li>
    <span class="talk-date text-muted">{{ talk.date | date: "%b %-d, %Y" }}</span>
    <a href="{{ talk.url | relative_url }}">{{ talk.title }}</a>
    &mdash; {{ talk.speaker_names }}
    {% if talk.recording %}<a href="{{ talk.recording }}" target="_blank" rel="noopener">[recording]</a>{% endif %}
    {% if talk.slides %}<a href="{{ talk.slides }}" target="_blank" rel="noopener">[slides]</a>{% endif %}
  </li>
  {% if forloop.last %}</ul>{% endif %}
{% endfor %}

---

<p class="text-muted">
Talk records live in <code>_data/talks/</code> as TOML files; the pages above are generated from them.
See the <a href="https://github.com/utah-datascience/utah-datascience.github.io/blob/master/README.md#talks">README</a>
for how to add one.
</p>
