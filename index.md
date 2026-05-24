---
layout: default
title: Home | Engineering Tech Insight
---

<style>
    .posts-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
        gap: 30px;
        margin-top: 40px;
    }
    .post-card {
        background-color: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 25px;
        transition: all 0.3s ease;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .post-card:hover {
        transform: translateY(-5px);
        border-color: #2563eb;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05);
    }
    .post-card-category {
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        color: #2563eb;
        background-color: #eff6ff;
        padding: 4px 10px;
        border-radius: 20px;
        display: inline-block;
        margin-bottom: 15px;
    }
    .post-card-title {
        font-size: 1.4rem;
        font-weight: 700;
        color: #111827;
        line-height: 1.3;
        margin-bottom: 10px;
        letter-spacing: -0.5px;
    }
    .post-card-date {
        font-size: 0.9rem;
        color: #6b7280;
        font-weight: 500;
        margin-top: auto;
    }
</style>

# Latest Tech Analysis

<div class="posts-grid">
  {% for post in site.posts %}
    <a href="{{ post.url | relative_url }}" class="post-card">
        <div>
            {% if post.category %}
                <span class="post-card-category">{{ post.category }}</span>
            {% endif %}
            <h3 class="post-card-title">{{ post.title }}</h3>
        </div>
        <p class="post-card-date">{{ post.date | date: "%B %d, %Y" }}</p>
    </a>
  {% endfor %}
</div>
