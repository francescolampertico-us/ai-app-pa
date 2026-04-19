import unittest
from pathlib import Path
import sys

EXEC_DIR = Path(__file__).resolve().parent
if str(EXEC_DIR) not in sys.path:
    sys.path.insert(0, str(EXEC_DIR))

from clean_clip import _llm_api_key, _post_process_llm, _responses_api_url, clean_clip, validate_output


class CleanClipReutersRegressionTest(unittest.TestCase):
    def test_changeagent_uses_changeagent_env(self) -> None:
        env = sys.modules['clean_clip'].os.environ
        old_openai_base = env.get("OPENAI_BASE_URL")
        old_changeagent_base = env.get("CHANGE_AGENT_BASE_URL")
        old_changeagent_key = env.get("CHANGE_AGENT_API_KEY")
        old_model_override = env.get("LLM_MODEL_OVERRIDE")
        try:
            env["CHANGE_AGENT_BASE_URL"] = "https://example.test/v1/"
            env["CHANGE_AGENT_API_KEY"] = "ca_test_key"
            env["LLM_MODEL_OVERRIDE"] = "ChangeAgent"
            self.assertEqual(_responses_api_url("ChangeAgent"), "https://example.test/v1/responses")
            self.assertEqual(_llm_api_key("ChangeAgent"), "ca_test_key")
        finally:
            if old_openai_base is None:
                env.pop("OPENAI_BASE_URL", None)
            else:
                env["OPENAI_BASE_URL"] = old_openai_base
            if old_changeagent_base is None:
                env.pop("CHANGE_AGENT_BASE_URL", None)
            else:
                env["CHANGE_AGENT_BASE_URL"] = old_changeagent_base
            if old_changeagent_key is None:
                env.pop("CHANGE_AGENT_API_KEY", None)
            else:
                env["CHANGE_AGENT_API_KEY"] = old_changeagent_key
            if old_model_override is None:
                env.pop("LLM_MODEL_OVERRIDE", None)
            else:
                env["LLM_MODEL_OVERRIDE"] = old_model_override

    def test_reuters_article_chrome_is_removed(self) -> None:
        raw = """Exclusive news, data and analytics for financial market professionals
World

Business

Markets

Haiti, Dominican Republic to reopen airspace in May
By Reuters
April 17, 20264:37 PM EDTUpdated 23 hours ago

April 17 (Reuters) - Haiti and the Dominican Republic agreed to open the airspace between the two countries starting in May, according to a statement on Friday, after flights had been suspended more than two years earlier.

"This measure aims to facilitate mobility, boost economic ties and strengthen relations between the two countries," the countries said in a joint statement.

The Reuters Iran Briefing newsletter keeps you informed with the latest developments and analysis of the Iran war. Sign up here.
Reporting by Jesus Frias; Writing by Natalia Siniawski; Editing by Kylie Madry

Our Standards: The Thomson Reuters Trust Principles., opens new tab

Suggested Topics:

Read Next

Mexico mends ties with Spain in first presidential visit in eight years

Reuters, the news and media division of Thomson Reuters, is the world’s largest multimedia news provider.
All quotes delayed a minimum of 15 minutes. See here for a list of exchanges and delays.
© 2026 Reuters. All rights reserved
"""
        expected = (
            "Haiti and the Dominican Republic agreed to open the airspace between the two countries "
            "starting in May, according to a statement on Friday, after flights had been suspended "
            "more than two years earlier.\n\n"
            "\"This measure aims to facilitate mobility, boost economic ties and strengthen relations "
            "between the two countries,\" the countries said in a joint statement."
        )

        cleaned = clean_clip(raw, title="Haiti, Dominican Republic to reopen airspace in May")

        self.assertEqual(cleaned, expected)

    def test_post_process_llm_strips_generic_chrome_and_preserves_paragraphs(self) -> None:
        raw_output = """U.S.
For Haitians, Stampede at Citadelle Laferrière Mars a Bright Spot
See more of our coverage in your search results.
Bernard Mokam covers breaking news.
PORT-AU-PRINCE, Haiti (AP) —
Haitians cut back on already scarce food and ask how they’ll survive rising fuel prices.
WASHINGTON —
House considers bill to protect Haitian immigrants in pushback against Trump administration.
People visit the Citadelle Laferriere in Milot, Haiti April 26, 2024. REUTERS/Ricardo Arduengo/File Photo Purchase Licensing Rights, opens new tab
Leave your feedback
Share Copy URL https://www.pbs.org/newshour/politics/example
April 12, 2026"""

        cleaned = _post_process_llm(
            raw_output,
            title="For Haitians, Stampede at Citadelle Laferrière Mars a Bright Spot",
        )

        self.assertEqual(
            cleaned,
            "Haitians cut back on already scarce food and ask how they’ll survive rising fuel prices.\n\n"
            "House considers bill to protect Haitian immigrants in pushback against Trump administration.",
        )
        ok, issues = validate_output(
            cleaned,
            title="For Haitians, Stampede at Citadelle Laferrière Mars a Bright Spot",
        )
        self.assertTrue(ok, msg=str(issues))

    def test_post_process_llm_strips_title_and_city_prefix_when_combined_on_same_line(self) -> None:
        raw_output = (
            "U.S. For Haitians, Stampede at Citadelle Laferrière Mars a Bright Spot "
            "PORT-AU-PRINCE, Haiti (AP) — Haitians cut back on already scarce food and ask how they’ll survive rising fuel prices."
        )

        cleaned = _post_process_llm(
            raw_output,
            title="For Haitians, Stampede at Citadelle Laferrière Mars a Bright Spot",
        )

        self.assertEqual(
            cleaned,
            "Haitians cut back on already scarce food and ask how they’ll survive rising fuel prices.",
        )

    def test_post_process_llm_preserves_us_when_it_is_real_body_text(self) -> None:
        raw_output = (
            "Haitians cut back on already scarce food.\n"
            "U.S. officials said the policy would remain under review."
        )

        cleaned = _post_process_llm(raw_output, title=None)

        self.assertEqual(
            cleaned,
            "Haitians cut back on already scarce food.\n\n"
            "U.S. officials said the policy would remain under review.",
        )

    def test_local_cleaner_removes_nyt_section_label_and_google_prompt(self) -> None:
        raw = """U.S.

At least 30 people were killed when a crushing crowd formed at the entrance to the fortress in northern Haiti. The Citadelle is one of the country’s most famous sites.

See more of our coverage in your search results.

Add The New York Times on Google"""

        cleaned = clean_clip(raw, title=None)

        self.assertEqual(
            cleaned,
            "At least 30 people were killed when a crushing crowd formed at the entrance to the fortress in northern Haiti. The Citadelle is one of the country’s most famous sites.",
        )

    def test_local_cleaner_strips_prefixed_pbs_share_block_and_dateline(self) -> None:
        raw = """By — Lisa Mascaro, Associated Press Lisa Mascaro, Associated Press Leave your feedback Share Copy URL https://www.pbs.org/newshour/politics/example Email Facebook Twitter LinkedIn Pinterest Tumblr Share on Facebook Share on Twitter House considers bill to protect Haitian immigrants in pushback against Trump administration Politics Apr 16, 2026 9:29 AM EDT WASHINGTON (AP) — In a rare bipartisan moment, the House has agreed to consider legislation that would extend temporary protections for Haitian immigrants. READ MORE: Surging oil prices spark protest in Haiti as workers demand salary increases A free press is a cornerstone of a healthy democracy. Support trusted journalism and civil dialogue. Donate now By — Lisa Mascaro, Associated Press Lisa Mascaro, Associated Press"""

        cleaned = clean_clip(
            raw,
            title="House considers bill to protect Haitian immigrants in pushback against Trump administration",
        )

        self.assertEqual(
            cleaned,
            "In a rare bipartisan moment, the House has agreed to consider legislation that would extend temporary protections for Haitian immigrants.",
        )

    def test_local_cleaner_strips_attached_date_prefix(self) -> None:
        raw = "April 12, 2026At least 30 people were killed and dozens more hospitalized after a stampede at a historical fortress in Haiti on Saturday."
        cleaned = clean_clip(raw, title=None)
        self.assertEqual(
            cleaned,
            "At least 30 people were killed and dozens more hospitalized after a stampede at a historical fortress in Haiti on Saturday.",
        )

    def test_local_cleaner_stops_before_press_release_chronology_tail(self) -> None:
        raw = """WASHINGTON – Today, Congresswoman Ayanna Pressley’s effort to extend Temporary Protected Status for Haiti was successfully adopted.

Yesterday, Rep. Pressley and Congresswoman Gillen held a press conference alongside colleagues and advocates calling for the extension of Temporary Protected Status (TPS) for Haitians.

- On June 28, 2025, Congresswoman Ayanna Pressley issued the following statement condemning the Trump Administration’s termination of TPS for Haiti.

- On June 5, 2025, Congresswoman Ayanna Pressley and Yvette D. Clarke issued the following statement on Donald Trump’s executive order."""

        cleaned = clean_clip(raw, title="BREAKING: Pressley Measure to Extend Haiti TPS Adopted by House")

        self.assertEqual(
            cleaned,
            "Today, Congresswoman Ayanna Pressley’s effort to extend Temporary Protected Status for Haiti was successfully adopted.\n\n"
            "Yesterday, Rep. Pressley and Congresswoman Gillen held a press conference alongside colleagues and advocates calling for the extension of Temporary Protected Status (TPS) for Haitians.",
        )

    def test_local_cleaner_stops_before_faq_and_disclaimer_tail(self) -> None:
        raw = """For many Haitian families in the United States, Temporary Protected Status is not an abstract policy debate.

This week, the House of Representatives passed a bill to extend TPS for Haiti through 2029.

Q: Did the House really pass a bill to extend Haiti TPS?

A: Yes. The House passed legislation on April 16, 2026, by a 224-204 vote.

Disclaimer: This article is for general informational purposes only and does not create an attorney-client relationship."""

        cleaned = clean_clip(raw, title="House Votes to Extend Haiti TPS")

        self.assertEqual(
            cleaned,
            "For many Haitian families in the United States, Temporary Protected Status is not an abstract policy debate.\n\n"
            "This week, the House of Representatives passed a bill to extend TPS for Haiti through 2029.",
        )

    def test_local_cleaner_removes_photo_credit_and_footer_boilerplate(self) -> None:
        raw = """Hungary's Prime Minister Viktor Orbán salutes supporters in Budapest, April 12. Attila Kisbenedek/Agence France-Presse/Getty Images

Authorities said the election result could reshape the regional balance.

Photo: Attila Kisbenedek/Agence France-Presse/Getty Images
REUTERS/Marton Monus
D.C., Md., & Va. washingtonpost.com © 1996-2026 The Washington Post"""

        cleaned = clean_clip(raw, title=None)

        self.assertEqual(
            cleaned,
            "Authorities said the election result could reshape the regional balance.",
        )

    def test_local_cleaner_removes_author_bio_and_print_edition_junk(self) -> None:
        raw = """The government signaled that coalition talks may intensify this week.

Walter Russell Mead is the Ravenel B. Curry III Distinguished Fellow in Strategy and Statesmanship at Hudson Institute, the Global View Columnist at The Wall Street Journal and the Alexander Hamilton Professor of Strategy and Statecraft with the Hamilton School for Classical and Civic Education at the University of Florida.
Before joining Hudson, Mr. Mead was a fellow at the Council on Foreign Relations as the Henry A. Kissinger Senior Fellow for U.S. Foreign Policy.
He has authored numerous books, including the widely-recognized Special Providence: American Foreign Policy and How It Changed the World (Alfred A. Knopf, 2004).
The column appears on the Wall Street Journal’s website every Monday evening and Tuesdays in print.
Copyright ©2026 Dow Jones & Company, Inc. All Rights Reserved. 87990cbe856818d5eddac44c7b1cdeb8 Appeared in the April 14, 2026, print edition as 'The Curtain Falls for Hungary’s Orbán'."""

        cleaned = clean_clip(raw, title=None)

        self.assertEqual(
            cleaned,
            "The government signaled that coalition talks may intensify this week.",
        )

    def test_local_cleaner_removes_related_posts_calendar_and_footer(self) -> None:
        raw = """Loading...

Union urges FG to ease mobility to boost intra-African trade

In "Business"

FG increases Unity Schools’ tuition to N100,000

In "Education"

S M T W T F S

5 6 7 8 9 10 11

12 13 14 15 16 17 18

19 20 21 22 23 24 25

The Federal Radio Corporation of Nigeria, FRCN, Africa’s largest radio network with six zonal stations operating on short and medium wave bands and two operations centres...

@2021 - radionigeria.gov.ng. All Right Reserved.

Corporate FM Stations Rate Card Radio Nigeria Investment Limited FOI Portal Staff Mail Click Naija Radio About Us"""

        cleaned = clean_clip(raw, title=None)

        self.assertEqual(cleaned, "")


if __name__ == "__main__":
    unittest.main()
