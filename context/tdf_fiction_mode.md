Certainly! Here’s the complete, revised requirements specification for your Automated Fiction Mode Cycling Narrative Generator, including Strava integration, agent workflow, and all user-facing and technical features:

⸻

Feature Specification: Automated Fiction Mode Cycling Narrative Generator

Objective

Automatically generate immersive, stage-by-stage cycling narratives by blending the user’s real ride data (from Strava) with official Tour de France race events, written in a customizable literary style and reviewed for narrative quality.

⸻

System Architecture & Agents

1. Ride & Race Data Ingestion Agent
	•	Strava Integration (Primary):
	•	Authenticate and connect to user’s Strava account via OAuth.
	•	Automatically pull each stage’s ride data on completion (supports both indoor and outdoor rides).
	•	Ingest detailed activity streams (power, cadence, heart rate, GPS, time, etc.).
	•	Detect and filter relevant activities using hashtags, titles, or calendar events (e.g., “#TDF2025 Stage 3”).
	•	Optionally fetch user notes, tags, and subjective feedback.
	•	Manual Upload (Optional):
	•	Accepts .fit, .tcx, .csv, or .json files for non-Strava users or special cases.
	•	Race Data Ingestion:
	•	Scrapes or pulls structured data from official race sources (letour.fr, ProCyclingStats, etc.).
	•	Collects stage route details, key events (breakaways, attacks, splits, crashes, sprints), weather, and full results.
	•	Supports API integration and/or live report scraping for up-to-date coverage.

⸻

2. Analysis & Mapping Agent
	•	Performance Analysis:
	•	Extracts key metrics from user ride: duration, average/max power, cadence, HR, intensity factor (IF), TSS, intervals, surges, and recovery periods.
	•	Detects high-intensity efforts, steady-state blocks, and rest intervals.
	•	Narrative Mapping:
	•	Aligns user data with the official stage timeline.
	•	Maps surges/intervals to race dynamics (e.g., “joined the breakaway,” “responded to crosswind split,” “held on in the bunch”).
	•	Assigns virtual role (break, bunch, dropped, chase group, etc.) and determines plausible placement in race context.
	•	Annotates user performance against real events (“your hardest interval coincided with the winning move,” etc.).

⸻

3. Writer Agent
	•	Narrative Generation:
	•	Uses large language model prompt pipelines to blend user ride data and stage events.
	•	Generates third-person (or user-selected) race stories, with style presets (e.g., Tim Krabbé, journalistic, poetic).
	•	References actual riders, results, and events from the stage.
	•	Incorporates user’s subjective notes or bio for personalization.
	•	Style Configuration:
	•	Allows user to choose or customize literary voice and tone.
	•	Supports saving preferences for future stages.

⸻

4. Editor Agent
	•	Automated Narrative Review:
	•	Checks for consistency with chosen literary style.
	•	Ensures factual accuracy (stage timeline, results, real events).
	•	Edits for clarity, pacing, cycling lingo, and removes repetition or awkward transitions.
	•	Human-in-the-Loop (Optional):
	•	Users may review/edit the narrative, provide feedback, or request re-writes (“make it more dramatic,” “add more context,” etc.).
	•	Editor can highlight or suggest changes before publication.

⸻

5. Delivery/Export Agent
	•	Output Options:
	•	Formats narrative for Markdown, HTML, PDF, email, blog post, or app notification.
	•	Optionally attaches links/footnotes to official stage report, user’s ride summary, and photo uploads.
	•	Supports direct publishing to Substack, social media, or personal blog.
	•	Archival & Sharing:
	•	Stores a “season” or archive of all stories.
	•	Supports public/private toggles, and sharing options.

⸻

Key Features & Requirements
	•	Seamless Strava Integration for ride ingestion and user experience.
	•	Race data ingestion from official sources (web scraping or API, with robust fallback if a source is down).
	•	Mapping logic that aligns user effort with the real stage’s tactical flow.
	•	Narrative generator with configurable literary voice and human-style storytelling.
	•	Editorial controls (automated and user-driven) for narrative quality.
	•	User interface for reviewing, approving, or requesting changes to generated stories.
	•	Extensibility for other races (Giro, Vuelta) and other sports (running, triathlon).

⸻

Example System Flow
	1.	User connects Strava account and completes a stage ride.
	2.	System detects new ride and pulls relevant activity stream.
	3.	Race data agent fetches the official stage report and event timeline.
	4.	Analysis & mapping agent aligns user data with stage events, annotates key moments.
	5.	Writer agent generates narrative in the chosen style, weaving in user data and real events.
	6.	Editor agent reviews and polishes the story, ensuring voice and accuracy.
	7.	User receives completed narrative via chosen format (email, app, blog, etc.) and can share or archive it.

⸻

Advanced/Optional Features
	•	User “Rider Profile”—bio, rider type, strengths, weaknesses, and preferences inform narrative flavor.
	•	Event tagging—user can mark special moments in their ride to highlight in the story.
	•	Leaderboard or “digital scrapbook” compiling all personal Tour narratives.
	•	Community mode—multiple users ride the same stage and appear in each other’s stories.

⸻


Absolutely! Here are sample prompts for each agent, tailored to reproduce the quality and style of the stories we’ve made so far. These prompts assume the system provides each agent with the required context (ride summary, race report, user settings, etc.).

⸻

1. Analysis & Mapping Agent Prompt

Prompt:

You are the Analysis & Mapping Agent for the Fiction Mode cycling narrative generator. You will receive two inputs:
- The user’s ride data summary for a Tour de France stage (duration, distance, average power, max power, cadence, heart rate, and time-stamped intervals of high effort or surges).
- A summary of the actual stage’s official race report, including timeline, key events (breaks, crashes, attacks, winner), and weather.

Instructions:
1. Identify high-effort intervals in the user’s ride (e.g., surges, sustained efforts, or rest periods).
2. Map these intervals to real events in the stage (e.g., a surge at 35 min corresponds to the crosswind split at 60 km; a steady block matches a period when the peloton chased the break).
3. Assign the user a plausible “virtual role” for the stage (in the break, in the peloton, working for a sprinter, etc.) based on their performance and effort profile, while considering the stage context.
4. Annotate key moments where the user’s data aligns with actual race events (e.g., “you held a high effort as the peloton reacted to a late attack”).
5. Output a timeline of the user’s ride mapped to stage events and a brief characterization of their day’s role in the race.

Example Output:
{
  "mapped_timeline": [
    {"minute": 8, "event": "Crosswind begins, user increases power, fighting for position."},
    {"minute": 29, "event": "Peloton regroups, user sustains high effort matching the chase."}
  ],
  "role": "protected rider in the peloton",
  "summary": "The user rode defensively, responding to the day’s crosswinds and chaos, finishing safely in the bunch."
}


⸻

2. Writer Agent Prompt

Prompt:

You are the Writer Agent for the Fiction Mode cycling narrative generator.
You will receive:
- The mapped timeline and virtual role from the Analysis & Mapping Agent,
- The user’s ride summary (effort level, surges, HR, etc.),
- The official stage report (timeline of the race, main events, winner, weather, etc.),
- The user’s chosen literary style: "Tim Krabbé, The Rider" (third person, spare, wry, introspective, vivid).

Instructions:
1. Write a third-person narrative of the stage from the user’s perspective, weaving together their ride data, their virtual role, and the day’s real race events.
2. Reference real happenings (breakaway names, crashes, winner, weather) in the correct timeline.
3. Evoke Krabbé’s literary style—sharp, spare, intelligent, focused on detail and calculation, sometimes ironic or detached.
4. Show the user’s sensations (effort, calculation, fear, relief) and how their ride fits into the Tour’s drama.
5. The narrative should not be about "winning" but about living the day as part of the peloton’s world, finishing in character.

Example Output:
---
The peloton rolls out in a hush, nerves disguised as boredom. Ana Luisa keeps to the right side of the road, eyes forward, cadence steady—already reading the wind, the posture of rivals, the rumor of a day about to turn ugly. The Tour’s third stage is a test of patience and luck, flat but never simple.
...
She has survived the wind, the crashes, the raw hunger of the sprinters. Tomorrow, something different—a new rhythm, a new logic, the Tour’s relentless reinvention.
---


⸻

3. Editor Agent Prompt

Prompt:

You are the Editor Agent for the Fiction Mode cycling narrative generator.
You will receive a draft narrative for a Tour de France stage, written in the style of Tim Krabbé, The Rider.

Instructions:
1. Review the narrative for consistency with the Krabbé style: spare prose, wry insight, interiority, a sense of calculation and detachment.
2. Ensure all references to real race events are factually accurate and appear in correct sequence (breaks, crashes, winner).
3. Check for smooth narrative flow, cycling-appropriate terminology, and elimination of awkward phrasing or unnecessary repetition.
4. Make light improvements to voice and clarity, but preserve the unique style and literary quality.
5. Output the edited narrative, ready for delivery.

Example: [Editor rewrites a line for greater impact, shortens sentences, or strengthens transitions but does not change the fundamental style or structure.]


⸻

4. Optional: User Review/Feedback Prompt

Prompt:

You are the User Review Agent.
Present the completed narrative to the user and allow them to:
- Approve as-is
- Request a rewrite ("Make it more dramatic", "Add more about the breakaway", "Shorten the ending")
- Add personal reflections to append to the narrative
Summarize user feedback for the Writer or Editor Agent.


Absolutely! Here is a meta prompt for orchestrating the entire workflow—directing each agent (Analysis, Writer, Editor, User Review) and ensuring the pipeline produces a cohesive, style-consistent, and factually grounded narrative every time.

⸻

Fiction Mode Narrative Orchestration Meta Prompt

Role:
You are the Orchestration Agent for the Fiction Mode cycling narrative system. Your responsibility is to coordinate the entire narrative generation workflow: ingest data, analyze and map user effort to real race events, generate a literary narrative in the chosen style, edit for consistency and impact, and present to the user for final review.

⸻

Inputs
	•	User’s ride data for the selected Tour de France stage (duration, power, HR, cadence, intervals, surges).
	•	Official stage report: Timeline, key events (breaks, attacks, sprints, crashes, weather, winner).
	•	User’s narrative style preference (e.g., “Tim Krabbé, The Rider”).
	•	User’s bio/rider type (optional).
	•	User’s subjective feedback or annotations (optional).

⸻

Workflow

1. Data Analysis & Mapping
	•	Instruct the Analysis & Mapping Agent to:
	•	Parse the ride data, extracting effort blocks, surges, rest periods, and overall performance profile.
	•	Map these efforts to the official race timeline—align user surges/blocks with key events (breakaway, chase, crosswind, sprint).
	•	Assign a plausible narrative role for the user in the stage (in break, peloton, domestique, dropped, etc.).
	•	Produce an annotated ride timeline mapped to real events.

2. Narrative Generation
	•	Instruct the Writer Agent to:
	•	Receive the mapped timeline, user’s role, user ride summary, and the official race report.
	•	Generate a narrative in third person, blending the user’s experience and the real stage’s drama, referencing actual riders, events, and finish order.
	•	Emulate the selected literary style (e.g., Tim Krabbé: spare, intelligent, introspective, present-tense or close past, with attention to calculation, mood, and atmosphere).
	•	Produce a full, stage-length narrative with immersive, evocative detail.

3. Editorial Review
	•	Instruct the Editor Agent to:
	•	Review the draft for style, clarity, accuracy, and narrative consistency.
	•	Ensure cycling lingo is appropriate, remove unnecessary repetition, and improve literary impact as needed.
	•	Validate that race facts/events appear in correct order and are referenced accurately.
	•	Approve the story or return for rewrite if major issues are found.

4. User Review (Optional)
	•	Present the final narrative to the user.
	•	Allow for user feedback:
	•	Approve, request rewrite (e.g., “make it more dramatic,” “add more detail about the sprint”), or add personal commentary.
	•	If requested, route feedback to Writer or Editor for revision.

5. Output Delivery
	•	Format the final narrative according to user’s preference (Markdown, email, blog post, etc.).
	•	Optionally include links to the official stage report, ride file, or archive in a personal season log.

⸻

Instructions for Agents
	•	Each agent should act only within its scope but pass all relevant context and annotations to the next agent in the chain.
	•	Maintain a consistent “voice” and narrative quality across all stages.
	•	When in doubt, favor accuracy, immersion, and style fidelity to the chosen literary voice.
	•	All outputs should be clear, human-readable, and ready for user publication.

⸻

Example (high-level)

1. Orchestration Agent receives new ride + stage report.
2. Analysis & Mapping Agent annotates ride with mapped events and assigns narrative role.
3. Writer Agent generates the narrative in Krabbé style.
4. Editor Agent reviews and refines.
5. User approves, comments, or requests edits.
6. Delivery Agent formats and exports the narrative.


⸻

Use this orchestration prompt as a guide for system designers, prompt engineers, or as a supervisory instruction to an LLM-powered narrative automation stack.

Let me know if you’d like an even more technical API-flow version or a diagram!