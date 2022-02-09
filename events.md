---
layout: single
title: Events
date: 2022-03-25
header:
  title: Datathon
  excerpt: >
    The UofU datathon4justice is aimed at introducing undergraduates to the use of quantitative methods to address social issues.
  background-image: /assets/img/header-background/zion-shorter.jpg
---

### UofU Datathon4Justice
The UofU datathon4justice is aimed at introducing undergraduates to the use of quantitative methods to address social justice questions. The main event is a weekend-long datathon in which teams will tackle environmental justice problems relevant to our SLC community, featuring: keynote addresses by the founders of the Institute for the Quantitative Study of Inclusion, Diversity, and Equity (QSIDE); presentations from activists and researchers looking at local environmental justice questions; and team support from consultants in data science, environmental studies, and social justice. A number of preparatory workshops will be offered leading up to the main event; these workshops will cover a range of programming and data science topics, from introductory Python through specialized data processing toolboxes. Finally, teams will have two opportunities to present their work: first in a special datathon4justice session at the **Undergraduate Research Symposium on April 5**, second at the **SQuARED Justice Conference on April 22** organized by QSIDE.

The datathon has 3 main parts:
* Preparatory workshops before the event,
* The actual datathon, with keynote addresses and team work time + support,
* Opportunities to present your work.

All are welcome to attend the preparatory workshops without taking part in the datathon; see the "Workshops" section for more information (including the registration link). For those interested in taking part in the datathon, see the "Datathon" section.

Acknowledgements: this Datathon is made possible by support from the Office of Undergraduate Research and the Utah Center for Data Science.

### Dates and Details
* Date: March 25-26
* Format: hybrid
* Schedule:
  * Friday March 25 (location: WEB 1230)
    * 5.00pm - 5.10pm - Overview and announcements
    * 5.10pm - 5.35pm - Keynote by Jude Higdon and Chad Topaz of QSIDE
    * 5.35pm - 6.00pm - Keynote by activist/scientists related to problem/data
    * 6.00pm - 9.00pm - Group work time, with coaches available to answer questions
  * Saturday March 26 (location: WEB various rooms)
    * 9.00am - 12.00pm - Group work time, with coaches available to answer questions
    * 1.00pm - 3.30pm - Group work time, with coaches available to answer questions
    * 3.30pm - 4.15pm - Keynote by activist/scientists related to problem/data
    * 4.15pm - 4.30pm - Wrap-up by organizers, next-steps, etc. 
  * Tuesday April 5 (location: Union Building or virtual)
    * 10.45am - 12.15pm - Presentations by groups at the [Undergrad Research Symposium](https://our.utah.edu/events/undergraduate-research-symposium/).
  * Friday April 22 (location: virtual)
    * 10.00am - 6.00pm ET - [SQuARED Justice conference](https://qsideinstitute.org/events/square-conference/), where students are also invited to present their work during the poster session.

### Workshops
This series of workshops will give participants an introduction to programming and data analysis in preparation for the Datathon4Justice. Each workshop will be self-contained explorations of the Python programming language, from an introduction to programming up to advanced data analysis packages useful for the datathon.

To register for the preparatory workshops, please fill out [this short form](https://forms.gle/9qg7gLZHGnitxSuX9). The workshops will be offered in a hybrid format, with in-person registration capped to 20 people based on first-come-first-serve.

#### Workshop Schedule
* Beginner python for non-STEM/crash-course
  * Day/time: Wednesday Feb 23, 4:30 - 5:30 PM MST
  * Room: LCB 115
  * Abstract: Our first workshop will be geared towards those interested in the Datathon4Justice and have no background in computer science. We will begin with basic operations and variable types, then discuss control flows and functions. The goal is to introduce attendees to the language and structure of programming so that attendees can more effectively communicate with teammates. 
* Data analysis and special packages in Python
  * Day/time: Wednesday Mar 2, 4:30 - 5:30 PM MST
  * Room: LCB 115
  * Abstract: This workshop will introduce key packages in Python for data analysis. These packages will be used to read, manipulate, and plot data. This workshop will also discuss best practices for presentation of data in a report. Participants new to programming will get a sense for the advantages of analyzing data using programming languages over spreadsheets.
* Introduction to exploratory data analysis with a suicide dataset
  * Day/time: Wednesday March 16, 4:30 - 5:30 PM MST
  * Room: LCB 115
  * Abstract: This workshop will introduce exploratory data analysis which involves performing the initial investigation of a data set to begin to understand what questions the data set can answer. A real world sucide data set will be explored to showcase graphical and non graphical techniques used for exploratory data analysis. This workshop will provide participants the opportunity to apply the Python and data analysis skills they gained in the previous workshops to real world data.
* Special topic
  * Day/time: Wednesday March 23, 4:30 - 5:30 PM MST
  * Room: LCB 115
  * Abstract: Exact topics TBD. Options for the workshop include an exploration of the dataset to be used in the competition and advanced Python packages potentially applicable to the dataset.
  
### Datathon
The theme for this datathon is environmental justice. Teams will be provided data and questions sourced from environmental science researchers as well as local groups studying light pollution and public health, from an equity lens, in the Salt Lake City metro area. The questions will be presented in a tiered-format to match teams’ entry levels in data science and social justice: (1) low-entry level problems performing exploratory data analysis and study validation, (2) medium-entry level problems for more experienced teams interested in exploring more novel aspects, including starting to address open-ended questions, and (3) high-entry level problems for experienced data scientists and activists, aimed at providing highly motivated teams an entry point into active environmental justice research.

To register for the actual datathon, please fill out [this short form](https://forms.gle/ZPxMbVXgKjBXuZaq6). Rooms in WEB are reserved and will be provided to teams on a first-come-first-serve basis, so be sure to register early! **Registration is open until March 11, 2022**.

Data and questions will be released shortly before the event, along with consultant schedules and contact means for the weekend.

### COVID policy

Events are live and in-person. The keynote addresses will be live and in-person, and recorded. To support in-person participation during the datathon, we will provide hand sanitizer, masks, and a spacious setup.

![Office of Undergraduate Research, The University of Utah]({{ '/events/2022_datathon/assets/OUR_Logo.jpg' | relative_url }}){:class="img-fluid"}

---

### Past Events
{% assign events = site.pages | where:"categories","dataday" |sort: "date" | reverse %}
{% for eventpage in events %}
* [{{ eventpage.title }}]({{ eventpage.url }})
{% endfor %}
