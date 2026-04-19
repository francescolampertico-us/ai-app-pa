# Example 02 — Output (review-first run summary)

report_artifact:
- /Users/francescolampertico/Downloads/media_clips_jan29.docx

email_artifacts:
- /Users/francescolampertico/Downloads/media_clips_jan29_email.txt
- /Users/francescolampertico/Downloads/media_clips_jan29_email.html

review_behaviour:
- initial list loads with light-cleaned previews
- each article expands inline for author edit, text edit, manual paste, remove, and deeper cleanup
- final report uses the reviewed article text and author values

observed_index_examples:
- A Bus Maker Withstood One Year of Trump's Tariffs. New Challenges Loom.
- Are Trump's tariffs fueling a boom in trade deals for China and India?
- Reliance Eyes Lower Russian Oil Imports as India Cuts Dependence.
- Opinion | The EU-India Trade Deal Is Boring, and That's a Good Thing.

notes:
- This example reflects the current review-first app workflow, not the older all-at-once cleanup flow.
- Deeper article cleanup uses the configured LLM-compatible endpoint only when the reviewer invokes it for a selected article.
