import content_generator
import performance_tracker
import optimizer

def run_pipeline():
    print("\n" + "="*60)
    print("  NOVAMIND AI MARKETING PIPELINE")
    print("="*60)

    topic = input("\nEnter a blog topic (e.g. 'AI in creative automation'): ").strip()
    if not topic:
        topic = "AI in creative automation"

    print("\n[STEP 1] Generating content with Gemini...")
    content, content_file = content_generator.run(topic)

    print("\n[STEP 2] Pushing to HubSpot CRM...")
    try:
        import crm_manager
        campaigns = crm_manager.run(content)
    except Exception as e:
        print(f"  ⚠️  HubSpot step skipped: {e}")
        print("  Using mock campaign data for performance step...")
        from datetime import datetime
        campaigns = {
            persona: {
                "campaign_id": f"NM-MOCK-{persona[:4].upper()}",
                "newsletter_subject": content["newsletters"][persona]["subject"],
                "contact_count": 2,
                "sent_at": datetime.now().isoformat(),
            }
            for persona in content["newsletters"]
        }

    print("\n[STEP 3] Analyzing performance...")
    report = performance_tracker.run(content["blog"]["title"], campaigns)

    print("\n[STEP 4] Running AI content optimization...")
    opt = optimizer.run(content, report)

    print("\n" + "="*60)
    print("✅ Pipeline complete!")
    print(f"   Blog: {content['blog']['title']}")
    print(f"   Personas: {', '.join(content['newsletters'].keys())}")
    print(f"   Campaigns: {len(campaigns)}")
    print(f"\n💡 Suggested next topics:")
    for i, t in enumerate(opt["suggested_topics"], 1):
        print(f"   {i}. {t['topic']}")
    print("="*60)

if __name__ == "__main__":
    run_pipeline()
