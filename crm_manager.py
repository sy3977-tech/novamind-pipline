import json
import os
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
HUBSPOT_API_KEY = os.getenv("HUBSPOT_API_KEY")
BASE_URL = "https://api.hubapi.com"
HEADERS = {
    "Authorization": f"Bearer {HUBSPOT_API_KEY}",
    "Content-Type": "application/json",
}

# Mock contacts for each persona
MOCK_CONTACTS = {
    "creative_professional": [
        {"firstname": "Emma", "lastname": "Chen", "email": "emma.chen@designstudio.com", "company": "Chen Design Studio"},
        {"firstname": "Marcus", "lastname": "Rivera", "email": "marcus@pixelcraft.io", "company": "Pixelcraft Agency"},
    ],
    "startup_founder": [
        {"firstname": "Priya", "lastname": "Patel", "email": "priya@launchpad.co", "company": "Launchpad Inc"},
        {"firstname": "Jake", "lastname": "Williams", "email": "jake@buildfast.io", "company": "BuildFast"},
    ],
    "marketing_manager": [
        {"firstname": "Sarah", "lastname": "Thompson", "email": "s.thompson@growthco.com", "company": "GrowthCo"},
        {"firstname": "David", "lastname": "Kim", "email": "dkim@marketingpros.com", "company": "Marketing Pros"},
    ],
}


def create_or_update_contact(contact: dict, persona: str) -> str:
    """Create a contact in HubSpot and return its ID."""
    payload = {
        "properties": {
            "firstname": contact["firstname"],
            "lastname": contact["lastname"],
            "email": contact["email"],
            "company": contact["company"],
            "novamind_persona": persona,
        }
    }
    res = requests.post(f"{BASE_URL}/crm/v3/objects/contacts", headers=HEADERS, json=payload)
    if res.status_code == 409:
        search_res = requests.post(
            f"{BASE_URL}/crm/v3/objects/contacts/search",
            headers=HEADERS,
            json={"filterGroups": [{"filters": [{"propertyName": "email", "operator": "EQ", "value": contact["email"]}]}]},
        )
        contact_id = search_res.json()["results"][0]["id"]
        requests.patch(f"{BASE_URL}/crm/v3/objects/contacts/{contact_id}", headers=HEADERS, json=payload)
        return contact_id
    elif res.status_code == 201:
        return res.json()["id"]
    else:
        print(f"  ⚠️  Could not create contact {contact['email']}: {res.text}")
        return None


def log_campaign(blog_title: str, persona: str, newsletter_subject: str, contact_ids: list) -> str:
    """Log a campaign send as a HubSpot note (engagement)."""
    campaign_id = f"NM-{datetime.now().strftime('%Y%m%d%H%M%S')}-{persona[:4].upper()}"
    note_body = (
        f"CAMPAIGN: {campaign_id}\n"
        f"Blog: {blog_title}\n"
        f"Persona: {persona}\n"
        f"Newsletter Subject: {newsletter_subject}\n"
        f"Sent to {len(contact_ids)} contacts\n"
        f"Date: {datetime.now().isoformat()}"
    )
    payload = {
        "properties": {
            "hs_note_body": note_body,
            "hs_timestamp": str(int(datetime.now().timestamp() * 1000)),
        },
        "associations": [
            {"to": {"id": cid}, "types": [{"associationCategory": "HUBSPOT_DEFINED", "associationTypeId": 202}]}
            for cid in contact_ids if cid
        ],
    }
    res = requests.post(f"{BASE_URL}/crm/v3/objects/notes", headers=HEADERS, json=payload)
    if res.status_code == 201:
        print(f"  📋 Campaign logged: {campaign_id}")
    else:
        print(f"  ⚠️  Could not log campaign: {res.text}")
    return campaign_id


def run(content: dict) -> dict:
    """Push all contacts + newsletters to HubSpot and log campaigns."""
    blog_title = content["blog"]["title"]
    campaigns = {}

    print("\n🔗 Connecting to HubSpot...")

    for persona, newsletter in content["newsletters"].items():
        print(f"\n👥 Processing persona: {persona}")
        contacts = MOCK_CONTACTS[persona]
        contact_ids = []

        for contact in contacts:
            print(f"  ➕ Creating/updating contact: {contact['email']}")
            cid = create_or_update_contact(contact, persona)
            if cid:
                contact_ids.append(cid)
                print(f"     ✅ Contact ID: {cid}")

        print(f"  📨 'Sending' newsletter: {newsletter['subject']}")
        campaign_id = log_campaign(blog_title, persona, newsletter["subject"], contact_ids)

        campaigns[persona] = {
            "campaign_id": campaign_id,
            "newsletter_subject": newsletter["subject"],
            "contact_ids": contact_ids,
            "sent_at": datetime.now().isoformat(),
            "contact_count": len(contact_ids),
        }

    # Save campaign log locally
    os.makedirs("output/campaigns", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"output/campaigns/crm_log_{timestamp}.json"
    with open(log_file, "w", encoding="utf-8") as f:
        json.dump({"blog_title": blog_title, "campaigns": campaigns}, f, indent=2)

    print(f"\n✅ CRM log saved to {log_file}")
    return campaigns


if __name__ == "__main__":
    # Load the most recent content file for testing
    import glob
    files = sorted(glob.glob("output/campaigns/content_*.json"))
    if not files:
        print("❌ No content file found. Run content_generator.py first.")
        exit(1)
    with open(files[-1], encoding="utf-8") as f:
        content = json.load(f)
    run(content)
