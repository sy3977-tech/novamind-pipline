import json
import os
import random
from datetime import datetime
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = "llama-3.3-70b-versatile"

# Simulated performance ranges per persona (based on marketing benchmarks)
PERFORMANCE_PROFILES = {
    "creative_professional": {"open_rate": (0.38, 0.52), "click_rate": (0.12, 0.22), "unsubscribe_rate": (0.005, 0.015)},
    "startup_founder":       {"open_rate": (0.30, 0.45), "click_rate": (0.08, 0.18), "unsubscribe_rate": (0.008, 0.020)},
    "marketing_manager":     {"open_rate": (0.35, 0.48), "click_rate": (0.10, 0.20), "unsubscribe_rate": (0.006, 0.016)},
}


def simulate_performance(campaigns: dict) -> dict:
    """Generate realistic mock engagement metrics for each campaign."""
    metrics = {}
    for persona, campaign in campaigns.items():
        profile = PERFORMANCE_PROFILES.get(persona, {"open_rate": (0.25, 0.40), "click_rate": (0.05, 0.15), "unsubscribe_rate": (0.005, 0.02)})
        count = campaign.get("contact_count", 2)
        open_rate = round(random.uniform(*profile["open_rate"]), 4)
        click_rate = round(random.uniform(*profile["click_rate"]), 4)
        unsub_rate = round(random.uniform(*profile["unsubscribe_rate"]), 4)
        metrics[persona] = {
            "campaign_id": campaign["campaign_id"],
            "newsletter_subject": campaign["newsletter_subject"],
            "contacts_sent": count,
            "open_rate": open_rate,
            "click_rate": click_rate,
            "unsubscribe_rate": unsub_rate,
            "opens": round(count * open_rate),
            "clicks": round(count * click_rate),
            "unsubscribes": round(count * unsub_rate),
            "recorded_at": datetime.now().isoformat(),
        }
    return metrics


def generate_ai_summary(blog_title: str, metrics: dict) -> str:
    """Use Gemini to write a performance analysis and recommendations."""
    metrics_text = ""
    for persona, m in metrics.items():
        metrics_text += (
            f"\nPersona: {persona}\n"
            f"  Open rate: {m['open_rate']*100:.1f}%\n"
            f"  Click rate: {m['click_rate']*100:.1f}%\n"
            f"  Unsubscribe rate: {m['unsubscribe_rate']*100:.2f}%\n"
        )

    prompt = f"""You are a marketing analyst for NovaMind, an AI startup.

A newsletter campaign was sent for blog post: "{blog_title}"

Performance metrics:
{metrics_text}

Write a short performance summary (150-200 words) that:
1. Highlights which persona performed best and why
2. Flags any concerns (e.g. high unsubscribe rate)
3. Gives 2-3 concrete recommendations for the next campaign

Be specific, data-driven, and actionable. Write in plain text, no bullet points."""

    response = client.chat.completions.create(
        model=MODEL, messages=[{"role": "user", "content": prompt}], temperature=0.7
    )
    return response.choices[0].message.content.strip()


def run(blog_title: str, campaigns: dict) -> dict:
    print("\n📊 Simulating campaign performance data...")
    metrics = simulate_performance(campaigns)

    print("🤖 Generating AI performance summary...")
    summary = generate_ai_summary(blog_title, metrics)

    report = {
        "blog_title": blog_title,
        "report_generated_at": datetime.now().isoformat(),
        "metrics_by_persona": metrics,
        "ai_summary": summary,
    }

    os.makedirs("output/campaigns", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"output/campaigns/performance_{timestamp}.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Performance report saved to {report_file}")
    print("\n" + "="*60)
    print("AI PERFORMANCE SUMMARY")
    print("="*60)
    print(summary)
    print("="*60)
    return report


if __name__ == "__main__":
    import glob
    crm_files = sorted(glob.glob("output/campaigns/crm_log_*.json"))
    if not crm_files:
        print("❌ No CRM log found. Run crm_manager.py first.")
        exit(1)
    with open(crm_files[-1], encoding="utf-8") as f:
        crm_data = json.load(f)
    run(crm_data["blog_title"], crm_data["campaigns"])
