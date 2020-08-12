---
layout: single
title: Members
header:
  title: Members
  background-image: /assets/img/header-background/zion-shorter.jpg
---

<style>
img.member {
  width: 200px;
  height: 286px;
  object-fit: cover;
  /* black and white */
  -webkit-filter: grayscale(100%); /* Safari 6.0 - 9.0 */
  filter: grayscale(100%);
}
</style>

{% assign roles = "Director,Associate Director of Research,Associate Director of Outreach,Associate Director of Student-Engagement,Core Members,Affiliated Members" | split: "," %}

{% for role in roles %}
<div style="margin-bottom: 1rem">
  <h2 style="margin-bottom: 1rem">{{ role }}</h2>
  {% assign members_list = site.members | where: "role", role %}
  {% for member in members_list %}
  <div class="row" style="margin-bottom: 1rem">
    <div class="col-lg-3">
      {% if member.pic contains "://" %}
      {% capture img_path %}{{ member.pic }}{% endcapture %}
      {% else %}
      {% capture img_path %}{{ member.pic | relative_url }}{% endcapture %}
      {% endif %}
      <a href="{{ member.link }}" target="_blank">
      <img src="{{ img_path }}" alt="Picture of {{ member.name }}" class="rounded shadow member">
        </a>
    </div>
    <div class="col-lg-9">
        <h4><a href="{{ member.link }}" target="_blank">{{ member.name }}</a></h4>
        <h6>{{ member.title | newline_to_br }}</h6>
      <p>{{ member.content | markdownify }}</p>
    </div>
  </div>
  {% endfor %}
</div>
{% endfor %}

---

### Organization and By-Laws

The UCDS is led by a director, with the assistance of associate directors and the other core members.  The Associate Direct or Research organizes research-focused events like the <a href="seminar.html">Data Science Seminar</a>.  The Associate Director of Outreach builds relations with other researchers around campus, including through the annual <a href="dataday.html">Data Science Day</a>.  And the Associate Director of Student Involvement leads efforts to engage students in data science, including as liason to associated <a href="club.html">student groups</a>. The Affiliated members represents the centers connections around campus into the many disciplines where data science reaches.

[Governance Roles](./assets/file/UCDS-Elections[7996].pdf)

[Membership Plans](./assets/file/UCDS-Affiliate[7995].pdf)
