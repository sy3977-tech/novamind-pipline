import json
import os
from datetime import datetime
from groq import Groq
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = "llama-3.3-70b-versatile"

PERSONAS = {
    "creative_professional": "a freelance designer or creative director at a small agency who wants to save time on repetitive tasks",
    "startup_founder": "a non-technical startup founder who wants to automate their team's daily workflows without hiring engineers",
    "marketing_manager": "a marketing manager at a mid-size company exploring AI tools to scale content production",
}

def generate_blog(topic: str) -> dict:
    print(f"\n✍️  Generating blog for: '{topic}'...")
    prompt = f"""You are a content writer for NovaMind, an AI startup helping creative agencies automate workflows.

Write a blog post about: "{topic}"

Return ONLY valid JSON (no markdown, no backticks) with this exact structure:
{{
  "title": "Blog title here",
  "outline": ["point 1", "point 2", "point 3", "point 4", "point 5"],
  "draft": "Full blog draft of 400-600 words here..."
}}"""

    response = client.chat.completions.create(
        model=MODEL, messages=[{"role": "user", "content": prompt}], temperature=0.7
    )
    text = response.choices[0].message.content.strip()
    if "```" in text:
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text.strip())


def generate_newsletters(topic: str, blog_title: str) -> dict:
    newsletters = {}
    for persona_key, persona_desc in PERSONAS.items():
        print(f"📧  Generating newsletter for: {persona_key}...")
        prompt = f"""You are writing a short promotional newsletter email for NovaMind.

Target audience: {persona_desc}
Blog topic: "{topic}"
Blog title: "{blog_title}"

Write a short, personal newsletter (150-200 words) promoting this blog post to this specific audience.

Return ONLY valid JSON (no markdown, no backticks):
{{
  "subject": "Email subject line here",
  "body": "Newsletter body text here..."
}}"""

        response = client.chat.completions.create(
            model=MODEL, messages=[{"role": "user", "content": prompt}], temperature=0.7
        )
        text = response.choices[0].message.content.strip()
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        newsletters[persona_key] = json.loads(text.strip())
    return newsletters


def run(topic: str) -> tuple:
    blog = generate_blog(topic)
    newsletters = generate_newsletters(topic, blog["title"])

    result = {
        "topic": topic,
        "generated_at": datetime.now().isoformat(),
        "blog": blog,
        "newsletters": newsletters,
    }

    os.makedirs("output/campaigns", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"output/campaigns/content_{timestamp}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"\n✅  Content saved to {filename}")
    return result, filename


if __name__ == "__main__":
    topic = input("Enter a blog topic: ")
    result, filename = run(topic)
    print(f"\n📄 Blog title: {result['blog']['title']}")
    print(f"📬 Newsletters generated for: {list(result['newsletters'].keys())}")
