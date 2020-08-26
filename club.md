---
layout: single
title: Data Science Club
header:
  title: Data Science Club
  excerpt: |
    Our mission is to help students learn about data science and machine learning through tutorials, presentations from industry professionals, and hands-on experience.
    
    <a href="http://mailman.cs.utah.edu/mailman/listinfo/ucds-seminar" target="_blank">join our mailing list</a>
    {: class="btn btn-neutral" }
    <br>
    
    [coordinators](/club/coordinators)
    {: class="btn btn-neutral"}  
---

<style>
img.speaker {
  width: 200px;
  height: 286px;
  object-fit: cover;
}
</style>

## [Summer Seminar Series](/club/summer-seminar-series)

<!-- Upcoming speaker. Assumes the next speaker is always at the top of the yml file -->
{% assign speaker = site.data.summer_speakers['2020'][0] %}

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
        {% if speaker.personal_site != null %}
          <h4><a href="{{ speaker.personal_site }}" target="_blank">{{ speaker.name }}</a></h4>
        {% else %}
          <h4>{{ speaker.name }}</h4>
        {% endif %}
        <h6>Presenting {{ speaker.date }} @ {{ speaker.time }} MDT</h6>
        <h6>Venue: {{ speaker.venue }}</h6>
        <h6>Title: {{ speaker.title }}. Abstract <a href="{{ speaker.filename | prepend: "/club/sss-2020/" }}" target="_blank" style="text-decoration:underline;">here</a>.</h6>
        <p>{{ speaker.bio }}</p>
    </div>
  </div>
</div>


## Want to get in touch with us?

We'd love for you to reach out to us about any events you'd like to happen, ideas you have, or interest you have in becoming involved in club leadership! To contact us directly, email Vivek Gupta at [keviv9@gmail.com](mailto:keviv9@gmail.com) or Kori South at [korianns@ymail.com](mailto:korianns@ymail.com).

---

## Resources

Below are some resources to help you on your journey to learn data science! These resources only scratch the surface, so if you come across anything you find useful or enlightening please reach out to the club leadership so we can put it here.

### FREE Summer 2020 Coursera Subscription
* The University of Utah's Office of Continuing Education & Community Engagement is providing free Coursera Subscriptions to all students and employees. Registration is open until July 31. Register [here](https://continue.utah.edu/coursera){:target="_blank"}.



### Python Introduction
* [Google for Education Python Introduction](https://developers.google.com/edu/python/){:target="_blank"}
* [Intro to Python Programming, Udacity](https://www.udacity.com/course/introduction-to-python--ud1110){:target="_blank"}

### Intro to Machine Learning
* [Harvard's Free Introduction to AI Course](https://www.edx.org/course/cs50s-introduction-to-artificial-intelligence-with-python){:target="_blank"}
* [How to Learn Data Science and Machine Learning](http://blog.kaggle.com/2017/04/17/the-best-sources-to-study-machine-learning-and-ai-with-ben-hamner-kaggle-cto/){:target="_blank"}
* [A Visual Introduction to Machine Learning](http://www.r2d3.us/visual-intro-to-machine-learning-part-1/){:target="_blank"}
* [Data Science Tutorials on Kaggle](http://blog.kaggle.com/category/tutorials/){:target="_blank"}
[Intro to Machine Learning, Udacity](https://www.udacity.com/course/intro-to-machine-learning--ud120){:target="_blank"}
* [Machine Learning Online Course, Coursera](https://www.coursera.org/learn/machine-learning){:target="_blank"}
* [Free Kaggle Machine Learning Tutorial](http://blog.kaggle.com/2016/04/25/free-kaggle-machine-learning-tutorial-for-python/){:target="_blank"}

### Deep Learning
* [Visual and Interactive Guide to Neural Networks](http://jalammar.github.io/visual-interactive-guide-basics-neural-networks/){:target="_blank"}
* [Neural Networks Demystified (Video Series)](https://www.youtube.com/watch?v=bxe2T-V8XRs){:target="_blank"}
* [Learn Deep Learning with Keras](http://p.migdal.pl/2017/04/30/teaching-deep-learning.html){:target="_blank"}
* [Digit Recognition with Keras](http://machinelearningmastery.com/handwritten-digit-recognition-using-convolutional-neural-networks-python-keras/){:target="_blank"}