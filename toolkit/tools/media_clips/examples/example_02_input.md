# Example 02 — Input (review-first workflow)

topic: India Media Clips
queries:
  - '"Trump" AND "India"'
  - '"Trump" AND "H1B Visa"'
  - '"Trump" AND "Tariff" AND "India"'
  - '"Trump" AND "Modi"'
  - '"Senate" AND "India"'
  - '"Senator" AND "India"'
  - '"Ambassador Vinay Kwatra"'
  - '"Sergio Gor" AND "India"'
  - '"Trump" AND "India" AND "Russia"'
  - '"Embassy of India"'
  - '"Indian Embassy"'
  - '"H1B Visa"'
  - '"US" AND "India"'
  - '"U.S." AND "India"'
period: 24h
source_filter: mainstream media only
max_clips: 10
workflow_expectations:
  - generate fast light-cleaned previews first
  - review each article inline
  - edit author and article text manually when needed
  - run deeper cleanup only on selected articles
  - build the final report from the reviewed clips set
