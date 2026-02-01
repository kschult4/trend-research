#!/usr/bin/env python3
"""
CrewAI Strategic Intelligence Crew - Criterion 2: Minimal Viable Crew
Scout + Analyst agents for trend monitoring
"""

import os
import yaml
from datetime import datetime
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from tools.source_fetcher import SourceFetcher

# Load environment variables
load_dotenv('config/.env')

# Initialize source fetcher (24 hours for initial test)
fetcher = SourceFetcher(lookback_hours=24)

# Load source configuration
with open('config/sources.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Fetch content from all active sources
print("[Crew] Fetching content from sources...")
all_entries = []
for source in config['sources']:
    if source['active'] and source['type'] == 'rss':
        entries = fetcher.fetch_rss(source['url'], source['name'])
        all_entries.extend(entries[:5])  # Limit to 5 entries per source

# Limit total entries to 15 for manageable context
all_entries = all_entries[:15]

# Format for Scout
source_content = fetcher.format_for_scout(all_entries)
print(f"[Crew] Fetched {len(all_entries)} total entries (limited for test)\n")

# === SCOUT AGENT ===
scout = Agent(
    role='Trend Scout',
    goal='Monitor AI/automation/homelab sources and tag signals by significance',
    backstory="""You are an experienced technology scout with deep expertise in 
    AI tooling, automation, and homelab systems. You excel at filtering signal 
    from noise and recognizing when a development is truly significant versus 
    just incremental progress.
    
    Your job is to read through recent content and identify signals worth 
    tracking. You categorize each signal by significance:
    
    🔴 MILESTONE - Major shift, paradigm change, need to know now
    🟡 MOVEMENT - Trend building momentum, worth tracking
    ⚪ NOISE - Logged for context but not immediately relevant
    
    You focus on: practical tools, adoption patterns, workflow changes, 
    new capabilities that solve real problems.""",
    verbose=True,
    allow_delegation=False,
    llm='claude-3-haiku-20240307'
)

# === ANALYST AGENT ===
analyst = Agent(
    role='Pattern Analyst',
    goal='Synthesize patterns across Scout signals and identify emerging themes',
    backstory="""You are a strategic analyst who excels at connecting dots 
    across disparate signals. You see patterns before they become obvious. 
    You think in terms of implications, not just features.
    
    Your job is to take the Scout's tagged signals and synthesize them into 
    insights. You look for convergence, contradictions, gaps, and acceleration.
    
    You write analysis that is concise, opinionated, and actionable.""",
    verbose=True,
    allow_delegation=False,
    llm='claude-3-haiku-20240307'
)

# === SCOUT TASK ===
scout_task = Task(
    description=f"""Analyze the following content from AI/automation/homelab sources.
    Identify and tag signals by significance level.
    
    CONTENT TO ANALYZE:
    {source_content}
    
    For each signal you identify:
    1. Assign significance: 🔴 Milestone, 🟡 Movement, or ⚪ Noise
    2. Extract the core signal (what changed, what's new)
    3. Note the source
    4. Be selective - not every item is worth flagging
    
    Output format:
    ## 🔴 Milestone Signals
    [List any milestone signals with brief description]
    
    ## 🟡 Movement Signals  
    [List movement signals with brief description]
    
    ## ⚪ Noise (Context Only)
    [List noise signals briefly]
    """,
    agent=scout,
    expected_output="Tagged signals organized by significance level with descriptions"
)

# === ANALYST TASK ===
analyst_task = Task(
    description="""Take the Scout's tagged signals and synthesize patterns across them.
    
    Your analysis should include:
    1. Emerging Patterns - What themes or directions are appearing?
    2. Implications - What do these patterns suggest about where things are heading?
    3. Open Questions - What gaps or contradictions deserve attention?
    
    Be concise but insightful. Focus on synthesis, not just summary.
    
    Output a well-structured analysis section.""",
    agent=analyst,
    expected_output="Synthesized analysis identifying patterns, implications, and open questions",
    context=[scout_task]
)

# === CREW ORCHESTRATION ===
crew = Crew(
    agents=[scout, analyst],
    tasks=[scout_task, analyst_task],
    process=Process.sequential,
    verbose=True
)

# === EXECUTE ===
print("\n" + "="*80)
print("STARTING CREW EXECUTION")
print("="*80 + "\n")

try:
    result = crew.kickoff()
    
    # Get individual task outputs
    scout_output = scout_task.output.raw if hasattr(scout_task, 'output') else "Scout output not available"
    analyst_output = str(result)
    
    # === SAVE OUTPUT ===
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_file = f"output/digest_{timestamp}.md"
    
    with open(output_file, 'w') as f:
        f.write(f"# Strategic Intelligence Digest\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Sources Monitored:** {len(config['sources'])}\n")
        f.write(f"**Signals Analyzed:** {len(all_entries)}\n\n")
        f.write("---\n\n")
        f.write("# Scout Report\n\n")
        f.write(scout_output)
        f.write("\n\n---\n\n")
        f.write("# Analyst Synthesis\n\n")
        f.write(analyst_output)
        f.write("\n\n---\n\n")
        f.write("*Generated by CrewAI Strategic Intelligence Crew (Criterion 2)*\n")
    
    print(f"\n\n[Crew] Output saved to: {output_file}")
    print(f"[Crew] Execution complete!")
    
except Exception as e:
    print(f"\n\n[ERROR] Crew execution failed: {str(e)}")
    import traceback
    traceback.print_exc()
