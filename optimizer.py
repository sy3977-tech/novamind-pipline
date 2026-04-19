import json
import glob
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = "llama-3.3-70b-versatile"


def chat(prompt: str) -> str:
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8,
    )
    return response.choices[0].message.content.strip()


def suggest_next_topics(performance_data: dict) -> dict:
    metrics = performance_data.get("metrics_by_persona", {})
    blog_title = performance_data.get("blog_title", "")
    ai_summary = performance_data.get("ai_summary", "")

    metrics_text = "\n".join([
        f"- {persona}: open={m['open_rate']*100:.1f}%, click={m['click_rate']*100:.1f}%"
        for persona, m in metrics.items()
    ])

    prompt = f"""You are a content strategist for NovaMind, an AI startup helping creative agencies automate workflows.

Previous blog: "{blog_title}"
Performance summary: {ai_summary}
Metrics:
{metrics_text}

Based on this engagement data, suggest 5 next blog topics that would likely perform even better.
For each topic, explain in one sentence WHY it would resonate based on the data.

Return ONLY valid JSON (no markdown, no backticks):
{{
  "suggested_topics": [
    {{"topic": "topic title here", "reason": "one sentence reason based on data"}},
    {{"topic": "topic title here", "reason": "one sentence reason based on data"}},
    {{"topic": "topic title here", "reason": "one sentence reason based on data"}},
    {{"topic": "topic title here", "reason": "one sentence reason based on data"}},
    {{"topic": "topic title here", "reason": "one sentence reason based on data"}}
  ]
}}"""

    text = chat(prompt)
    if "```" in text:
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text.strip())


def generate_alternative_headlines(blog_title: str, blog_draft: str) -> dict:
    prompt = f"""You are a copywriter for NovaMind, an AI startup.

Original blog title: "{blog_title}"
Blog content (first 300 chars): "{blog_draft[:300]}..."

Generate 5 alternative headlines for A/B testing. Each should have a different angle:
1. Curiosity-driven
2. Data/number-led
3. Problem-focused
4. Benefit-focused
5. Bold/provocative

Return ONLY valid JSON (no markdown, no backticks):
{{
  "alternatives": [
    {{"style": "Curiosity-driven", "headline": "headline here"}},
    {{"style": "Data/number-led", "headline": "headline here"}},
    {{"style": "Problem-focused", "headline": "headline here"}},
    {{"style": "Benefit-focused", "headline": "headline here"}},
    {{"style": "Bold/provocative", "headline": "headline here"}}
  ]
}}"""

    text = chat(prompt)
    if "```" in text:
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text.strip())


def suggest_newsletter_revisions(newsletter_body: str, persona: str, metrics: dict) -> dict:
    """Suggest specific revisions to a newsletter based on its performance."""
    open_rate = metrics.get("open_rate", 0)
    click_rate = metrics.get("click_rate", 0)
    unsub_rate = metrics.get("unsubscribe_rate", 0)

    prompt = f"""You are an email marketing expert for NovaMind.

Persona: {persona}
Newsletter performance: open={open_rate*100:.1f}%, click={click_rate*100:.1f}%, unsubscribe={unsub_rate*100:.2f}%
Original newsletter body:
{newsletter_body}

Based on the performance metrics, suggest specific revisions to improve this newsletter.
Focus on what to change and why based on the numbers.

Return ONLY valid JSON (no markdown, no backticks):
{{
  "diagnosis": "1-2 sentences on what the metrics tell us",
  "revisions": [
    {{"element": "subject line/opening/CTA/etc", "issue": "what's wrong", "suggestion": "specific fix"}},
    {{"element": "element name", "issue": "what's wrong", "suggestion": "specific fix"}},
    {{"element": "element name", "issue": "what's wrong", "suggestion": "specific fix"}}
  ],
  "revised_version": "Full revised newsletter body here..."
}}"""

    text = chat(prompt)
    if "```" in text:
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text.strip())


def run(content: dict, performance: dict) -> dict:
    """Run all optimizations and return results."""
    print("\n💡 Generating topic suggestions...")
    topics = suggest_next_topics(performance)

    print("📝 Generating alternative headlines...")
    headlines = generate_alternative_headlines(
        content["blog"]["title"],
        content["blog"]["draft"]
    )

    print("✏️  Generating newsletter revision suggestions...")
    # Pick the lowest click-rate persona for revision suggestions
    metrics = performance.get("metrics_by_persona", {})
    worst_persona = min(metrics, key=lambda p: metrics[p]["click_rate"]) if metrics else list(content["newsletters"].keys())[0]
    revisions = suggest_newsletter_revisions(
        content["newsletters"][worst_persona]["body"],
        worst_persona,
        metrics.get(worst_persona, {})
    )

    result = {
        "based_on_blog": content["blog"]["title"],
        "suggested_topics": topics["suggested_topics"],
        "alternative_headlines": headlines["alternatives"],
        "newsletter_revision": {
            "persona": worst_persona,
            **revisions
        }
    }

    os.makedirs("output/campaigns", exist_ok=True)
    from datetime import datetime
    filename = f"output/campaigns/optimization_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"✅  Optimization saved to {filename}")
    return result


if __name__ == "__main__":
    content_files = sorted(glob.glob("output/campaigns/content_*.json"))
    perf_files = sorted(glob.glob("output/campaigns/performance_*.json"))
    if not content_files or not perf_files:
        print("❌ Run main.py first to generate content and performance data.")
        exit(1)
    with open(content_files[-1], encoding="utf-8") as f:
        content = json.load(f)
    with open(perf_files[-1], encoding="utf-8") as f:
        performance = json.load(f)
    result = run(content, performance)
    print(f"\n📌 Suggested topics: {[t['topic'] for t in result['suggested_topics']]}")
