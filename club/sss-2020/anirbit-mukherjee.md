---
title: Summer Seminar Speaker
header:
  title: Summer Seminar Speaker
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

<center><a href="/club/summer-seminar-series"><<< Return to Summer Seminar Series</a></center>
<br>

{% assign name = page.name | replace: ".md", "" | downcase %}
{% assign speaker = site.data.summer_speakers['2020'] | where: "filename", name | first %}
<div style="margin-bottom: 1rem">
  <div class="row" style="margin-bottom: 1rem">
    <div class="col-lg-3">
      <img src="{{ speaker.img }}" alt="Picture of {{ speaker.name }}" class="rounded shadow speaker">
    </div>
    <div class="col-lg-9">
        <h2>
        {% if speaker.personal_site != null %}
        <a href="{{speaker.personal_site}}" target="_blank">{{speaker.name}}</a>
        {% else %}
        {{speaker.name}}
        {% endif %}
        </h2>
        <h6>Presenting {{ speaker.date }} @ {{ speaker.time }} MDT</h6>
        <p><div style="color:#cc3333; font-weight:bold; display:inline;">Venue: </div>{{ speaker.venue }}</p>
        <p><div style="color:#cc3333; font-weight:bold; display:inline;">Bio: </div>{{speaker.bio}}</p>        
    </div>
  </div>

  <!-- Row for title -->
  <div class="row" style="margin-bottom: 1rem">
    <h6>Talk Title: {{ speaker.title }}</h6>
  </div>
  
  <!-- Row for abstract -->
  <div class="row" style="margin-bottom: 1rem">
    <h6>Abstract: </h6>
    <p>{{speaker.abstract}}</p>
  </div>
</div>