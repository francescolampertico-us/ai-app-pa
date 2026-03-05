# Example 02 — Input (real AI-run directive)

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
trusted_sources:
  - Economist
  - New York Times
  - Washington Post
  - Wall Street Journal
  - USA Today
  - Politico
  - The Hill
  - Axios
  - Bloomberg
  - Reuters
  - AP
  - CNN
  - Fox News
  - CNBC
  - CBS
  - NBC
  - ABC
  - NPR
execution_mode: run via AI assistant using media_clips workflow directive
strict_format_requirements:
  - Font Calibri 11 for entire document
  - Title page centered bold
  - Index format: [Source]: [Title] - [Date]
  - Source bold in index
  - Title hyperlinked in index
  - Remove ".com" from source label
  - Remove weekday from date
