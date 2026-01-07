"""Mock data for demo environment - no database required"""

MOCK_AGENTS = [
    {
        "id": 1,
        "name": "Content Marketing Agent",
        "industry": "marketing",
        "specialty": "Healthcare",
        "rating": 4.9,
        "status": "available",
        "price": "₹12,000/month",
        "avatar": "CM",
        "activity": "Posted 23 times today",
        "retention": "98%",
        "description": "Specialized in healthcare content creation with deep industry knowledge",
    },
    {
        "id": 2,
        "name": "Math Tutor Agent",
        "industry": "education",
        "specialty": "JEE/NEET",
        "rating": 4.8,
        "status": "working",
        "price": "₹8,000/month",
        "avatar": "MT",
        "activity": "5 sessions today",
        "retention": "95%",
        "description": "Expert math tutor for competitive exam preparation",
    },
    {
        "id": 3,
        "name": "SDR Agent",
        "industry": "sales",
        "specialty": "B2B SaaS",
        "rating": 5.0,
        "status": "available",
        "price": "₹15,000/month",
        "avatar": "SDR",
        "activity": "12 leads generated",
        "retention": "99%",
        "description": "B2B sales development representative with proven track record",
    },
    {
        "id": 4,
        "name": "Social Media Agent",
        "industry": "marketing",
        "specialty": "B2B",
        "rating": 4.7,
        "status": "available",
        "price": "₹10,000/month",
        "avatar": "SM",
        "activity": "Posted 15 times today",
        "retention": "96%",
        "description": "Social media management for B2B companies",
    },
    {
        "id": 5,
        "name": "Science Tutor Agent",
        "industry": "education",
        "specialty": "CBSE",
        "rating": 4.9,
        "status": "available",
        "price": "₹8,000/month",
        "avatar": "ST",
        "activity": "8 sessions today",
        "retention": "97%",
        "description": "CBSE curriculum expert for grades 6-12",
    },
    {
        "id": 6,
        "name": "Account Executive Agent",
        "industry": "sales",
        "specialty": "Enterprise",
        "rating": 4.8,
        "status": "working",
        "price": "₹18,000/month",
        "avatar": "AE",
        "activity": "5 deals closing",
        "retention": "98%",
        "description": "Enterprise sales specialist",
    },
    {
        "id": 7,
        "name": "SEO Agent",
        "industry": "marketing",
        "specialty": "E-commerce",
        "rating": 4.6,
        "status": "available",
        "price": "₹11,000/month",
        "avatar": "SEO",
        "activity": "20 keywords ranked",
        "retention": "94%",
        "description": "E-commerce SEO optimization expert",
    },
]

MOCK_USERS = {}  # Store in-memory for demo


def get_agents(industry=None, min_rating=0.0):
    """Get agents with optional filters"""
    agents = MOCK_AGENTS

    if industry:
        agents = [a for a in agents if a["industry"] == industry]

    if min_rating:
        agents = [a for a in agents if a["rating"] >= min_rating]

    return agents


def get_agent_by_id(agent_id: int):
    """Get single agent by ID"""
    for agent in MOCK_AGENTS:
        if agent["id"] == agent_id:
            return agent
    return None


def create_user(email: str, name: str, google_id: str):
    """Create user in memory"""
    user_id = len(MOCK_USERS) + 1
    user = {
        "id": user_id,
        "email": email,
        "name": name,
        "google_id": google_id,
        "role": "viewer",
    }
    MOCK_USERS[google_id] = user
    return user


def get_user_by_google_id(google_id: str):
    """Get user by Google ID"""
    return MOCK_USERS.get(google_id)
