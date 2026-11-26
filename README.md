# Social Dots prompts

These are the exact prompts behind the AI videos and images that Social Dots, Ali Shafique and Zaira post. When a reel says "Comment PROMPT", this is where the prompt lives. Every prompt is free to read and use, with no email needed.

Each prompt file links to the posts it came from and to the finished result.

## The prompts

| Prompt | What it makes | Model |
|---|---|---|
| [cn-tower-builds-itself](prompts/cn-tower-builds-itself.md) | The CN Tower assembling itself from an empty lot at sunset, one drone shot | MiniMax H3, text to video |
| [toronto-city-hall-builds-itself](prompts/toronto-city-hall-builds-itself.md) | The same build, for Toronto City Hall | MiniMax H3, text to video |
| [cn-tower-fpv-drone-flight](prompts/cn-tower-fpv-drone-flight.md) | A low, fast FPV drone flight that orbits the CN Tower and opens onto the skyline | MiniMax H3, text to video |
| [cafe-time-freeze](prompts/cafe-time-freeze.md) | Time freezes in a cafe and one person keeps walking | MiniMax H3, reference to video |
| [potato-to-chip-bag-ad](prompts/potato-to-chip-bag-ad.md) | A potato peels, slices, fries and seals itself into a chip bag | MiniMax H3, text to video |
| [luxury-perfume-ad](prompts/luxury-perfume-ad.md) | A five-shot luxury perfume ad in golden smoke | MiniMax H3, reference to video |

## How to use a prompt

1. Open the prompt file and copy everything inside the grey box.
2. Fill in the blanks. A blank looks like `{{name}}` or `{{name: example}}`. The text after the colon is what we used in our post, so you can keep it or replace it with your own. Every blank with the same name takes the same value. Delete the braces when you are done.
3. Paste it into the model named at the top of the file and use the settings listed there: the aspect ratio, the length and, for reference-to-video prompts, how many photos of your person or product to upload.

The settings are the ones we rendered with. Most video tools that offer the same model let you pick the same aspect ratio and length, and the prompt works at higher resolutions too.

## Want this made for your business?

Social Dots makes AI video and marketing for local businesses. Book a free Growth Check-Up at [socialdots.ca](https://socialdots.ca) and we will show you what this would look like for you.

More free prompts, and the Social Dots prompt packs, are at [socialdots.ca/prompts](https://socialdots.ca/prompts).

## What is in each file

Every prompt is one Markdown file in `prompts/`, named after its id. The top of the file holds the details (title, model, settings, the posts it came from, where the finished result is hosted) and the body holds the exact prompt. The full format is in [docs/format.md](docs/format.md).

Some prompts were adapted from prompts other creators shared publicly. Those files link to the original in `adapted_from`, and the credit belongs to them.

## Privacy check

Every pull request and every push to `main` runs a check that blocks private material: client names, API keys and tokens, email addresses, phone numbers, internal file paths and Higgsfield element ids. Big media files are refused too, because results are hosted elsewhere and linked by URL. Run the checks locally before you push:

```sh
python3 -m pip install pyyaml
PRIVACY_DENYLIST="Client One, Client Two" python3 scripts/check_privacy.py --require-denylist
python3 scripts/check_prompts.py
python3 -m unittest discover -s tests
```

The list of client names is never stored in this repository, because the list itself would be private. In CI it comes from the `PRIVACY_DENYLIST` Actions secret. Locally, put one name per line in a `.privacy-denylist` file, which git ignores. A string that is safe to publish but trips the check can be added to `privacy-allowlist.txt`, with the reason given in the pull request.

## Licence

The prompts and documentation are shared under the Creative Commons Attribution 4.0 International licence (CC BY 4.0). See [LICENSE](LICENSE). Use them for anything, including client work, and credit Social Dots with a link back here.
