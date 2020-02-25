---
layout: home
header:
  title: Utah Center For Data Science
  title-color: default
  excerpt: >
    This center leads, organizes, and manages data science resources and research efforts at the University of Utah.  Its members advance the fundamental principles and practice of data science through research, applications, and community engagement.
  excerpt-color: black
  align: left
  background-image: /assets/img/header-background/lauren-pandolfi-midium.jpg
  bg-fill: white-bg
feature_row:
  - icon: ni ni-hat-3
    title: Academic Programs
    excerpt: The university has various different academic programs connected to data science.
    url: /programs.html
    btn_label: View details &raquo;
    btn_class: mt-4
    badge:
      - certification
      - degree
    color: danger
    icon_color: default
    badge_color: default
  - icon: fa fa-university
    title: Data Day
    excerpt: The 2019 Data Science Day will be held on October 18, 2019. More details to follow.
    url: #
    btn_label: View details &raquo;
    btn_class: mt-4
    badge:
      - research
      - conference
    color: danger
    icon_color: default
    badge_color: default
  - icon: fa fa-users
    title: Data Science Club
    excerpt: The data science club helps students learn about data science and machine learning through tutorial, presentations, and applications.
    url: #
    btn_label: View details &raquo;
    btn_class: mt-4
    badge:
      - tutorial
      - presentation
      - application
    color: danger
    icon_color: default
    badge_color: default
---

{% include feature_row.html %}


<section class="section section-lg pt-lg-0">
  <div class="container">
    <div class="row justify-content-center">
      <div class="col-lg-12">
 <h1>News <span class="left-icon"><a href="{{ site.baseurl }}/feed.xml"><i class="fa fa-rss"></i></a></span></h1>

  <ul class="post-list">
   {% assign news = site.posts | sort: 'date' %}
    {% for post in news reversed limit:4 %}
      <li class="post-list-item">
		   <div class="right-text">{{ post.date | date: "%-d %b %Y" }}</div>
        <div class="post-list-title">
          {{ post.title }}
        </div>
        <div class="post-list-excerpt">
		  {{ post.content | truncatewords: 160 }}
        </div>
  		<div><a class="post-list-link" href="{{ site.baseurl }}{{ post.url }}">More...</a></div>
      </li>
    {% endfor %}
  </ul>
  <div class="all-news-link"><a href="news">See All News</a></div>
 </div>
 </div>
 </div>
 </section>

<section class="section bg-secondary">
  <div class="container">
    <h2 class="mb-4">Upcoming Seminar Talk</h2>
    {% include next_talks.html %}
    <a href="{{ '/seminar.html' | relative_url }}" class="">See All Talks</a>
  </div>
</section>

