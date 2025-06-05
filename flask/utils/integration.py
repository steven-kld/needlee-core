import requests

def moodle(integration, score, review, logger):
    url = integration.get("api")
    if not url:
        logger("❌ No Moodle API URL provided")
        return False

    headers = {
        "Authorization": "Bearer yourSuperSecretTokenHere",
        "Content-Type": "application/json"
    }

    payload = {
        "userid": int(integration.get("user")),
        "courseid": int(integration.get("section")),
        "gradeitem": integration.get("grade"),
        "score": score,
        "review": review
    }

    try:
        res = requests.post(url, headers=headers, json=payload, timeout=15)
        if res.status_code == 200:
            logger("✅ Moodle push succeeded")
            return True
        else:
            logger(f"❌ Moodle error {res.status_code}: {res.text}")
            return False
    except Exception as e:
        logger(f"❌ Moodle push failed: {e}")
        return False

def run_integration(integration, score, review, logger):
    handlers = {
        "moodle": moodle,
    }

    handler = handlers.get(integration.get("in"))
    if handler:
        return handler(integration, score, review, logger)
    else:
        logger(f"⚠️ No integration handler for: {integration.get('in')}")
        return False