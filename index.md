---
layout: default
title: Engineering Tech Insight
show_hero: true
---

<!-- Category filter bar -->
<div class="filter-bar" role="navigation" aria-label="Filter posts by category">
  <span class="filter-label">Filter</span>
  <button class="filter-pill active" data-cat="All">All Posts</button>
  <button class="filter-pill" data-cat="Laptop">Laptops</button>
  <button class="filter-pill" data-cat="Mobile">Mobiles</button>
  <button class="filter-pill" data-cat="AI Tool">AI Tools</button>
</div>

<!-- Posts section -->
<div class="section-wrap">
  <div class="section-header">
    <h2 class="section-title">Latest Reviews</h2>
    <span class="section-count">{{ site.posts | size }} articles</span>
  </div>

  <div class="posts-grid" id="postsGrid" role="list">

    {% if site.posts.size == 0 %}
    <!-- Empty state -->
    <div class="empty-state" role="listitem">
      <div class="empty-state-icon" aria-hidden="true">📡</div>
      <p>Reviews are on the way. Check back soon.</p>
    </div>

    {% else %}

    {% for post in site.posts %}
      {% assign cat_raw = post.categories | first | default: post.category | default: "General" %}
      {% assign cat_lower = cat_raw | downcase | replace: " ", "-" %}

      {% comment %} Assign CSS class per category {% endcomment %}
      {% if cat_raw == "Laptop" %}
        {% assign tag_class = "laptop" %}
      {% elsif cat_raw == "Mobile" %}
        {% assign tag_class = "mobile" %}
      {% elsif cat_raw == "AI Tool" %}
        {% assign tag_class = "ai-tool" %}
      {% else %}
        {% assign tag_class = "mobile" %}
      {% endif %}

      {% comment %} Featured card = first post only {% endcomment %}
      {% if forloop.first %}
      <!-- ── Featured Post ─────────────────────────────────── -->
      <article class="post-card post-card--featured"
               data-cat="{{ cat_raw }}"
               role="listitem"
               onclick="location.href='{{ post.url | relative_url }}'">
        <div class="post-card-body">
          <div class="featured-badge" aria-label="Featured article">★ Featured</div>

          <div class="post-card-top">
            <span class="cat-tag {{ tag_class }}" aria-label="Category: {{ cat_raw }}">{{ cat_raw }}</span>
            <div class="post-card-arrow" aria-hidden="true">
              <svg viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="1.8">
                <path d="M2 10L10 2M10 2H4M10 2v6"/>
              </svg>
            </div>
          </div>

          <h3 class="post-card-title">{{ post.title }}</h3>

          {% if post.excerpt %}
          <p class="post-card-excerpt">{{ post.excerpt | strip_html | truncatewords: 45 }}</p>
          {% endif %}

          <div class="post-card-meta">
            <time class="post-card-date" datetime="{{ post.date | date_to_xmlschema }}">
              {{ post.date | date: "%b %d, %Y" }}
            </time>
            <span class="post-card-read">Read Review →</span>
          </div>
        </div>
      </article>

      {% else %}
      <!-- ── Regular Post Card ──────────────────────────────── -->
      <article class="post-card"
               data-cat="{{ cat_raw }}"
               role="listitem"
               onclick="location.href='{{ post.url | relative_url }}'">

        <div class="post-card-top">
          <span class="cat-tag {{ tag_class }}" aria-label="Category: {{ cat_raw }}">{{ cat_raw }}</span>
          <div class="post-card-arrow" aria-hidden="true">
            <svg viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="1.8">
              <path d="M2 10L10 2M10 2H4M10 2v6"/>
            </svg>
          </div>
        </div>

        <h3 class="post-card-title">{{ post.title }}</h3>

        {% if post.excerpt %}
        <p class="post-card-excerpt">{{ post.excerpt | strip_html | truncatewords: 30 }}</p>
        {% endif %}

        <div class="post-card-meta">
          <time class="post-card-date" datetime="{{ post.date | date_to_xmlschema }}">
            {{ post.date | date: "%b %d, %Y" }}
          </time>
          <span class="post-card-read">Read →</span>
        </div>
      </article>
      {% endif %}

    {% endfor %}
    {% endif %}

  </div><!-- /posts-grid -->
</div><!-- /section-wrap -->
