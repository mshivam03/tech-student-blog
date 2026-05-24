---
layout: default
title: Tech Student Blog
---

# Welcome to Shivam's Tech Blog 🚀

Hamare automatic AI engine dwara generate kiye gaye latest tech blogs, laptop reviews, aur gadgets ki jankari niche dekhein:

## Latest Posts
<ul>
  {% for post in site.posts %}
    <li>
      <a href="{{ post.url | relative_url }}">{{ post.title }}</a> — <i>{{ post.date | date: "%B %d, %Y" }}</i>
    </li>
  {% endfor %}
</ul>
