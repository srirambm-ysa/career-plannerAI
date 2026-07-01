import json
from openai import OpenAI
from flask import current_app


def _get_client():
    return OpenAI(
        base_url=current_app.config['OPENROUTER_BASE_URL'],
        api_key=current_app.config['OPENROUTER_API_KEY'],
        timeout=30,
    )


def _call_llm(system_prompt, user_prompt):
    client = _get_client()
    response = client.chat.completions.create(
        model=current_app.config['OPENROUTER_MODEL'],
        messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt},
        ],
        response_format={'type': 'json_object'},
        temperature=0.7,
    )
    content = response.choices[0].message.content
    return json.loads(content)


SYSTEM_TASKS = """You are a career analysis AI. Given a job title, industry, and years of experience,
generate exactly 12 specific, concrete daily or weekly tasks that a professional in this role performs.
Each task should be a single sentence, specific enough to evaluate for AI automation potential.
Categorize each task into one of: Analytical, Creative, Technical, Interpersonal, Administrative, Strategic.
Return JSON in this format:
{"tasks": [{"description": "...", "category": "..."}]}"""


def generate_tasks(job_title, industry, years_exp):
    user_prompt = (
        f"Job Title: {job_title}\n"
        f"Industry: {industry}\n"
        f"Years of Experience: {years_exp}\n\n"
        f"Generate 12 specific tasks for this role."
    )
    return _call_llm(SYSTEM_TASKS, user_prompt)


SYSTEM_RISK = """You are an AI risk assessment expert. For each task provided:
1. Rate its exposure to AI automation on a scale of 1 to 10:
   1 = Impossible to automate (requires deep human judgment, empathy, creativity)
   10 = Fully automatable today (routine, rule-based, data-driven)
2. Rate the task's importance to the role on a scale of 1 to 5:
   1 = Minor / peripheral task
   5 = Core / mission-critical task
Provide a brief 1-sentence explanation for each score.
Return JSON in this format:
{"tasks": [{"description": "...", "risk_score": 5, "importance": 3, "explanation": "..."}]}"""


def score_tasks(tasks):
    tasks_list = [t['description'] for t in tasks]
    user_prompt = (
        "Evaluate the following tasks for AI automation exposure. "
        "Return the same number of items in the same order.\n\n"
        + "\n".join(f"{i+1}. {t}" for i, t in enumerate(tasks_list))
    )
    return _call_llm(SYSTEM_RISK, user_prompt)


SYSTEM_ROADMAP = """You are a career strategist AI. Based on a professional's task-level AI risk profile,
generate a personalized upskilling roadmap. Recommend 6-8 skills ranked by priority (1 = highest).
For each skill:
- skill_name: Name of the skill
- priority: Integer 1-8
- timeline: "short" (0-3 months), "medium" (3-9 months), or "long" (9-18 months)
- description: 2-3 sentences on why this skill matters and how to develop it
- category: "Technical", "Soft Skill", "Strategic", "Creative", "AI Literacy"
- resources: Array of 2-3 strings (course names, books, tools)
Return JSON in this format:
{"roadmap": [{"skill_name": "...", "priority": 1, "timeline": "short", "description": "...", "category": "...", "resources": ["...", "..."]}]}"""


def generate_roadmap(tasks):
    risk_summary = "\n".join(
        f"- {t['description']}: Risk {t.get('risk_score', 'N/A')}/10 - {t.get('explanation', '')}"
        for t in tasks
    )
    user_prompt = (
        "Based on this professional's task-level AI risk profile, "
        "generate a strategic upskilling roadmap.\n\n"
        f"Risk Profile:\n{risk_summary}"
    )
    return _call_llm(SYSTEM_ROADMAP, user_prompt)
