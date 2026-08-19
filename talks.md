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

{%- comment -%} Distinct tags, speakers and years, for the filter controls. {%- endcomment -%}
{%- assign tag_index = "|" -%}
{%- assign speaker_index = "|" -%}
{%- assign year_index = "|" -%}
{%- for talk in all_talks -%}
  {%- for tag in talk.tags -%}
    {%- capture key %}{{ tag }}|{% endcapture -%}
    {%- unless tag_index contains key -%}{%- assign tag_index = tag_index | append: key -%}{%- endunless -%}
  {%- endfor -%}
  {%- for speaker in talk.speakers -%}
    {%- capture key %}{{ speaker.name }}|{% endcapture -%}
    {%- unless speaker_index contains key -%}{%- assign speaker_index = speaker_index | append: key -%}{%- endunless -%}
  {%- endfor -%}
  {%- capture key %}{{ talk.date | date: "%Y" }}|{% endcapture -%}
  {%- unless year_index contains key -%}{%- assign year_index = year_index | append: key -%}{%- endunless -%}
{%- endfor -%}
{%- assign tags = tag_index | remove_first: "|" | split: "|" | sort -%}
{%- assign speakers = speaker_index | remove_first: "|" | split: "|" | sort -%}
{%- assign years = year_index | remove_first: "|" | split: "|" | sort | reverse -%}

<style>
  .talk-list { list-style: none; padding-left: 0; }
  .talk-list li { margin-bottom: 1rem; }
  .talk-date { display: inline-block; min-width: 8.5rem; }
  .talk-filters { margin-bottom: 1.5rem; }
  .talk-filters .form-control { display: inline-block; width: auto; margin-right: .5rem; }
  .talk-tag {
    display: inline-block; margin: 0 .35rem .35rem 0; padding: .2rem .6rem;
    border: 1px solid #dee2e6; border-radius: 1rem; background: #fff;
    font-size: .8rem; color: #525f7f; cursor: pointer;
  }
  .talk-tag[aria-pressed="true"] { background: #5e72e4; border-color: #5e72e4; color: #fff; }
  .talk-item-tags { font-size: .75rem; color: #8898aa; }
  #talk-status { font-size: .9rem; color: #8898aa; }
  .talk-item[hidden], .talk-group[hidden] { display: none !important; }
</style>

<div class="talk-filters" id="talk-filters" hidden>
  <label class="sr-only" for="talk-q">Search talks</label>
  <input class="form-control" type="search" id="talk-q" style="min-width: 18rem;"
    placeholder="Search title, speaker, abstract&hellip;" autocomplete="off">

  <label class="sr-only" for="talk-speaker">Speaker</label>
  <select class="form-control" id="talk-speaker">
    <option value="">All speakers</option>
    {% for speaker in speakers %}<option value="{{ speaker | escape }}">{{ speaker }}</option>{% endfor %}
  </select>

  <label class="sr-only" for="talk-year">Year</label>
  <select class="form-control" id="talk-year">
    <option value="">All years</option>
    {% for year in years %}<option value="{{ year }}">{{ year }}</option>{% endfor %}
  </select>

  <button type="button" class="btn btn-sm btn-neutral" id="talk-reset">Clear</button>

  <div class="mt-3">
    {% for tag in tags %}
    <button type="button" class="talk-tag" data-tag="{{ tag | escape }}" aria-pressed="false">{{ tag }}</button>
    {% endfor %}
  </div>

  <p class="mt-3 mb-0" id="talk-status" role="status" aria-live="polite"></p>
</div>

{%- comment -%}
Every entry carries the fields the filters work on: `data-search` holds the
whole record (title, speakers, affiliations, tags, location, date, abstract)
lower-cased, so the search box covers all of them.
{%- endcomment -%}

<section class="talk-group" data-group="upcoming">
  <h2>Upcoming</h2>
  {% if upcoming.size > 0 %}
  <ul class="talk-list">
    {% for talk in upcoming %}{% include talk_list_item.html talk=talk %}{% endfor %}
  </ul>
  {% else %}
  <p>No talks scheduled right now. Check back soon, or
  <a href="https://mailman.cs.utah.edu/mailman3/lists/ucds-seminar.cs.utah.edu/">join the mailing list</a>.</p>
  {% endif %}
</section>

<h2>Past talks</h2>

{% assign current_year = "" %}
{% for talk in past %}
  {%- assign year = talk.date | date: "%Y" -%}
  {% if year != current_year %}
    {% unless forloop.first %}</ul></section>{% endunless %}
<section class="talk-group" data-group="{{ year }}">
<h3 id="y{{ year }}">{{ year }}</h3>
<ul class="talk-list">
    {% assign current_year = year %}
  {% endif %}
  {% include talk_list_item.html talk=talk %}
  {% if forloop.last %}</ul></section>{% endif %}
{% endfor %}

<p id="talk-empty" class="text-muted" hidden>No talks match those filters.</p>

<script>
  (function () {
    var filters = document.getElementById('talk-filters');
    if (!filters) return;
    filters.hidden = false; // the controls are useless without JS, so only show them here

    var query = document.getElementById('talk-q');
    var speaker = document.getElementById('talk-speaker');
    var year = document.getElementById('talk-year');
    var reset = document.getElementById('talk-reset');
    var status = document.getElementById('talk-status');
    var empty = document.getElementById('talk-empty');
    var tagButtons = Array.prototype.slice.call(filters.querySelectorAll('.talk-tag'));
    var items = Array.prototype.slice.call(document.querySelectorAll('.talk-item'));
    var groups = Array.prototype.slice.call(document.querySelectorAll('.talk-group'));

    function activeTags() {
      return tagButtons
        .filter(function (button) { return button.getAttribute('aria-pressed') === 'true'; })
        .map(function (button) { return button.dataset.tag; });
    }

    function apply() {
      var terms = query.value.toLowerCase().split(/\s+/).filter(Boolean);
      var tags = activeTags();
      var wantedSpeaker = speaker.value.toLowerCase();
      var wantedYear = year.value;
      var shown = 0;

      items.forEach(function (item) {
        var haystack = item.dataset.search;
        var itemTags = (item.dataset.tags || '').split('|');
        var visible =
          terms.every(function (term) { return haystack.indexOf(term) !== -1; }) &&
          (!tags.length || tags.some(function (tag) { return itemTags.indexOf(tag) !== -1; })) &&
          (!wantedSpeaker || (item.dataset.speakers || '').indexOf(wantedSpeaker) !== -1) &&
          (!wantedYear || item.dataset.year === wantedYear);
        item.hidden = !visible;
        if (visible) shown++;
      });

      groups.forEach(function (group) {
        var any = group.querySelector('.talk-item:not([hidden])');
        group.hidden = !any;
      });

      empty.hidden = shown !== 0;
      var filtered = terms.length || tags.length || wantedSpeaker || wantedYear;
      status.textContent = filtered
        ? shown + ' of ' + items.length + ' talks'
        : items.length + ' talks';
      remember(terms.length ? query.value : '', tags);
    }

    function remember(text, tags) {
      if (!window.history || !window.history.replaceState) return;
      var params = new URLSearchParams();
      if (text) params.set('q', text);
      tags.forEach(function (tag) { params.append('tag', tag); });
      if (speaker.value) params.set('speaker', speaker.value);
      if (year.value) params.set('year', year.value);
      var search = params.toString();
      window.history.replaceState(null, '', search ? '?' + search : window.location.pathname);
    }

    tagButtons.forEach(function (button) {
      button.addEventListener('click', function () {
        var on = button.getAttribute('aria-pressed') === 'true';
        button.setAttribute('aria-pressed', on ? 'false' : 'true');
        apply();
      });
    });

    query.addEventListener('input', apply);
    speaker.addEventListener('change', apply);
    year.addEventListener('change', apply);
    reset.addEventListener('click', function () {
      query.value = '';
      speaker.value = '';
      year.value = '';
      tagButtons.forEach(function (button) { button.setAttribute('aria-pressed', 'false'); });
      apply();
    });

    // Links such as /talks/?tag=robotics (from a talk page) arrive pre-filtered.
    var params = new URLSearchParams(window.location.search);
    if (params.get('q')) query.value = params.get('q');
    if (params.get('speaker')) speaker.value = params.get('speaker');
    if (params.get('year')) year.value = params.get('year');
    params.getAll('tag').forEach(function (tag) {
      tagButtons.forEach(function (button) {
        if (button.dataset.tag === tag) button.setAttribute('aria-pressed', 'true');
      });
    });
    apply();
  })();
</script>

---

<p class="text-muted">
Talk records live in <code>_data/talks/</code> as TOML files; the pages above are generated from them.
See the <a href="https://github.com/utah-datascience/utah-datascience.github.io/blob/master/README.md#talks">README</a>
for how to add one.
</p>
