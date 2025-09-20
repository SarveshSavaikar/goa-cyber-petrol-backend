import re
from typing import Dict, List, Tuple

# Hardcoded scammy keywords
SCAM_KEYWORDS = [
    "loan", "casino", "escort", "resort", "work from home", "earn daily",
    "gambling", "betting", "prostitute", "call girl", "massage", "dating",
    "fake", "fraud", "scam", "money back guarantee", "urgent", "limited time",
    "easy money", "get rich quick", "no investment", "lottery", "winner",
    "congratulations", "prize", "free money", "instant cash", "part time job"
]

# Takedown recommendations mapping
TAKEDOWN_RECOMMENDATIONS = {
    "scam": "Report to Cyber Cell",
    "fake_hotel": "Report to Tourism Dept",
    "prostitution": "Escalate for legal action",
    "gambling": "Escalate for legal action",
    "general_suspicious": "Monitor and investigate further"
}

def check_keywords(message_text: str) -> Tuple[int, str, str]:
    """
    Check message for suspicious keywords and calculate risk score.
    
    Returns:
        Tuple[risk_score, flagged_reason, takedown_recommendation]
    """
    message_lower = message_text.lower()
    matched_keywords = []
    
    # Check for keywords
    for keyword in SCAM_KEYWORDS:
        if keyword.lower() in message_lower:
            matched_keywords.append(keyword)
    
    if not matched_keywords:
        return 0, "No suspicious content detected", ""
    
    # Calculate risk score
    risk_score = 0
    keyword_count = len(matched_keywords)
    
    if keyword_count == 1:
        risk_score = 40
    elif keyword_count == 2:
        risk_score = 70
    else:
        risk_score = 85
    
    # Check for money amounts (₹\d+, INR pattern)
    money_pattern = r'(₹\s*\d+|INR\s*\d+|\d+\s*rupees?|Rs\.?\s*\d+)'
    if re.search(money_pattern, message_text, re.IGNORECASE):
        risk_score = min(90, risk_score + 20)
    
    # Determine category and takedown recommendation
    flagged_reason = f"Suspicious keywords detected: {', '.join(matched_keywords)}"
    
    # Categorize the type of suspicious content
    if any(word in matched_keywords for word in ["escort", "prostitute", "call girl", "massage", "dating"]):
        category = "prostitution"
    elif any(word in matched_keywords for word in ["casino", "gambling", "betting", "lottery"]):
        category = "gambling"
    elif any(word in matched_keywords for word in ["resort", "fake"]):
        category = "fake_hotel"
    else:
        category = "scam"
    
    takedown_recommendation = TAKEDOWN_RECOMMENDATIONS.get(category, TAKEDOWN_RECOMMENDATIONS["general_suspicious"])
    
    return risk_score, flagged_reason, takedown_recommendation

def is_high_risk(risk_score: int) -> bool:
    """Check if the risk score qualifies as high risk (70+)"""
    return risk_score >= 70