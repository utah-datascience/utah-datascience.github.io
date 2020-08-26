---
title: Summer Seminar Series
header:
  title: Summer Seminar Series
  excerpt: |
    Join our mailing list to receive the Seminar Zoom links via email.
    
    <a href="http://mailman.cs.utah.edu/mailman/listinfo/ucds-seminar" target="_blank">join our mailing list</a>
    {: class="btn btn-neutral" }
    <br>
    
    <a href="https://www.youtube.com/playlist?list=PLMsvlws5lSAb2cIyqmb7Ae7_omPK0m9hK" target="_blank">Seminar Recordings</a>
    {: class="btn btn-neutral" }
    <br>
    
    [coordinators](/club/coordinators)
    {: class="btn btn-neutral" }
---
<!-- Image styling -->
<style>
img.speaker {
  width: 200px;
  height: 286px;
  object-fit: cover;
}
</style>

<!-- The table of speakers -->
{% for speaker in site.data.summer_speakers['2020'] %}
{% assign more_info = speaker.filename | prepend: "/club/sss-2020/" %}
<div style="margin-bottom: 1rem">
  <div class="row" style="margin-bottom: 1rem">
    <div class="col-lg-3">
      <center>
        <img src="{{ speaker.img }}" alt="Picture of {{ speaker.name }}" class="rounded shadow speaker">
        {% if speaker.poster != null %}
          <p>Click <a href="{{ speaker.poster }}" target="_blank">here</a> for poster</p>
        {% endif %}
      </center>
    </div>
    <div class="col-lg-9">
        <h4>
        {% if speaker.personal_site != null %}
        <a href="{{speaker.personal_site}}" target="_blank">{{speaker.name}}</a>
        {% else %}
        {{speaker.name}}
        {% endif %}
        </h4>
        <h6>Presenting {{ speaker.date }} @ {{ speaker.time }} MDT</h6>
        <h6>Venue: {{ speaker.venue }}</h6>
        <h6>Title: {{ speaker.title }}. Click <a href="{{ more_info }}" style="text-decoration:underline;">here</a> for more info.</h6>
        <p>{{ speaker.bio }}</p>
    </div>
  </div>
</div>
---
{% endfor %}