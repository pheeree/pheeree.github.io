---
layout: default
title: "pheeree 읽기 노트"
---

{% assign latest = site.posts.first %}

{% if latest %}
<article class="post">
  <header class="post-header">
    <h1 class="post-title">{{ latest.title | escape }}</h1>
    <p class="post-meta">
      <time datetime="{{ latest.date | date_to_xmlschema }}">{{ latest.date | date: "%Y-%m-%d" }}</time>
      {% if latest.categories.size > 0 %} · {% for cat in latest.categories %}<span>{{ cat }}</span>{% unless forloop.last %}, {% endunless %}{% endfor %}{% endif %}
      · <a href="{{ latest.url | relative_url }}">영구 링크</a>
    </p>
  </header>

  <div class="post-content e-content">
    {{ latest.content }}
  </div>
</article>
{% else %}

아직 글이 없습니다.

{% endif %}

{% if site.posts.size > 1 %}

---

## 지난 글

<ul class="post-list">
{% for post in site.posts offset:1 %}
  <li>
    <time datetime="{{ post.date | date_to_xmlschema }}">{{ post.date | date: "%Y-%m-%d" }}</time>
    — <a href="{{ post.url | relative_url }}">{{ post.title | escape }}</a>
  </li>
{% endfor %}
</ul>

{% endif %}
