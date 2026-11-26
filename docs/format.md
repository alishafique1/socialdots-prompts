# Prompt file format

Every prompt is one file, `prompts/<id>.md`. It opens with YAML frontmatter between two `---` lines, followed by the prompt itself in a single fenced code block marked `text`. `scripts/check_prompts.py` enforces everything on this page, and the website (socialdots.ca/p/<id>) builds each prompt page from these fields, so nothing is hard-coded per page.

## Example

````markdown
---
id: cn-tower-builds-itself
title: "The CN Tower builds itself at sunset"
kind: video-generation
model: "MiniMax H3, text to video (turbo)"
settings:
  aspect_ratio: "9:16"
  width: 576
  height: 1024
  frames: 362
  duration_seconds: 15
  seed: 42
account: social-dots
posts:
  - platform: youtube
    status: posted
    at: "2026-11-25T00:01:50Z"
    url: "https://www.youtube.com/shorts/WDajKrJZylQ"
date: 2026-11-24
adapted_from: null
result:
  type: video
  url: "https://files.leadconnectorhq.com/file/.../clip.mp4"
  poster: null
  gallery: []
offer: free-growth-check-up
product: null
related: [toronto-city-hall-builds-itself]
blanks: []
---

```text
Vertical 9:16 photorealistic cinematic aerial video of ...
```
````

## Fields

Every field is required. A field with no value is written `null` (or `[]` for a list), never left out, so a missing value is always a choice and never an oversight.

| Field | What it holds |
|---|---|
| `id` | Lower-case slug, the same as the file name. It is also the page address: socialdots.ca/p/<id>. Never change it once a post links to it. |
| `title` | A short name for what the prompt makes. |
| `kind` | `video-generation`, `image-generation` or `claude-text`. |
| `model` | The model and mode the prompt was written for, in plain words. |
| `settings` | The settings we rendered with, as a mapping: aspect ratio, size, length, seed, number of reference images and so on. |
| `account` | The account that posted it: `social-dots`, `ali-shafique` or `zaira`. |
| `posts` | One entry per platform post: `platform` (instagram, tiktok, facebook, youtube, linkedin, x, threads or google), `status` (`posted` or `scheduled`), `at` (ISO date-time in UTC) and `url` (the public post link, required once posted, `null` while scheduled). |
| `date` | The day the prompt's first post went out, or is planned to, in Toronto time. |
| `adapted_from` | The public link to the creator's prompt this one was adapted from, or `null` when it is our own. |
| `result` | The finished result to embed above the prompt: `type` (`video` or `image`), `url` (the hosted MP4 or image), `poster` (a still frame for the player) and `gallery` (extra images, such as a before and after). The whole field may be `null` when nothing is hosted yet. |
| `offer` | The slug of the Social Dots service the page sells, for example `free-growth-check-up`, or `null`. |
| `product` | The slug of a live product that matches the prompt, for example a prompt pack, or `null`. Name only products that are on sale today. |
| `related` | Ids of other prompts to show under this one. Each must have its own file. |
| `blanks` | The names of the blanks used in the prompt. It must list exactly the names that appear in the body. |

## The prompt body

The body is exactly one fenced code block marked `text`, holding the prompt as it was used, so the copy button copies the whole thing and nothing else. Notes, tips and credits go in the frontmatter, not the body.

A blank is a part the reader should change. Write it `{{name}}` when there is no example, or `{{name: example}}` where the example is what we used in the post. Names are lower case with underscores. When the same blank appears more than once, repeat the same example each time so every copy reads correctly.

Anything private must become a blank before it is committed: a real person's description beyond what is public, reference photo paths, element ids, client names and brands.

## Media

Never commit videos or large images. Host the optimised MP4, poster and images on the website's storage, or reuse the public GoHighLevel media-library URL that was used for posting, and put the URLs in `result`. The format check refuses any media file over 300 KB.
