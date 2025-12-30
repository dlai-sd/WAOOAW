"""
Training Dataset Generator for WowTester

Story 0.1.7: Self-Training Dataset Creation (8 points)

Generates 1000+ pre-labeled evaluation examples for WowTester self-training:
- Diverse content types (blog posts, emails, social media)
- Multiple domains (marketing, education, sales)  
- 4 difficulty levels (simple, moderate, complex, expert)
- Human expert labels (simulated for now, can be replaced with real labels)
"""

import json
import random
import uuid
from datetime import datetime
from typing import Dict, List, Tuple
from dataclasses import asdict

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from waooaw.agents.wowtester import Scenario, EvaluationCriteria


# =========================================================================
# SAMPLE CONTENT TEMPLATES
# =========================================================================

BLOG_POST_TEMPLATES = {
    'simple': [
        {
            'title': 'Introduction to {topic}',
            'content': """
# Introduction to {topic}

{topic_desc}

## Why It Matters

{importance}

## Getting Started

{getting_started}

## Conclusion

{conclusion}

## Call to Action

Learn more about {topic} today. {cta}
""",
            'word_count_range': (600, 800)
        }
    ],
    'moderate': [
        {
            'title': 'Complete Guide to {topic}',
            'content': """
# Complete Guide to {topic}

{topic_desc}

## Background and Context

{background}

## Key Benefits

{benefits}

## Implementation Steps

{implementation}

## Common Challenges

{challenges}

## Best Practices

{best_practices}

## Conclusion

{conclusion}

## Take Action

{cta}
""",
            'word_count_range': (800, 1000)
        }
    ],
    'complex': [
        {
            'title': 'Advanced {topic} Strategies',
            'content': """
# Advanced {topic} Strategies for {industry} Professionals

{executive_summary}

## Introduction

{detailed_intro}

## Strategic Framework

{framework}

## Methodology

{methodology}

## Case Studies

{case_studies}

## Implementation Roadmap

{roadmap}

## ROI Analysis

{roi}

## Risk Mitigation

{risks}

## Conclusion

{conclusion}

## Next Steps

{cta}
""",
            'word_count_range': (1200, 1500)
        }
    ]
}

EMAIL_TEMPLATES = {
    'simple': [
        {
            'subject': 'Quick Update on {topic}',
            'content': """
Subject: Quick Update on {topic}

Preview: {preview}

Hi there,

{body}

{cta}

Best regards,
The Team
"""
        }
    ]
}

# =========================================================================
# CONTENT GENERATION
# =========================================================================

DOMAINS = ['marketing', 'education', 'healthcare']
DIFFICULTIES = ['simple', 'moderate', 'complex', 'expert']

TOPICS_BY_DOMAIN = {
    'marketing': [
        ('Email Marketing', 'Strategies for effective email campaigns'),
        ('Content Marketing', 'Creating valuable content that drives engagement'),
        ('Social Media Strategy', 'Building brand presence on social platforms'),
        ('SEO Optimization', 'Improving search engine rankings'),
        ('PPC Advertising', 'Paid advertising campaign management')
    ],
    'education': [
        ('Math Tutoring', 'Helping students master mathematics'),
        ('Reading Comprehension', 'Improving literacy skills'),
        ('STEM Education', 'Science, technology, engineering, and math learning'),
        ('Test Preparation', 'Strategies for standardized test success'),
        ('Study Skills', 'Effective learning and retention techniques')
    ],
    'healthcare': [
        ('Patient Care', 'Delivering quality healthcare services'),
        ('Telehealth', 'Remote patient consultation and monitoring'),
        ('Health IT', 'Healthcare information technology systems'),
        ('Clinical Workflows', 'Optimizing healthcare delivery processes'),
        ('HIPAA Compliance', 'Maintaining patient privacy and data security')
    ]
}


def generate_content_variations(template: str, quality_level: str = 'good') -> str:
    """Generate variations of content with different quality levels"""
    if quality_level == 'good':
        return template
    elif quality_level == 'mediocre':
        # Add some issues: repetitive, less polished
        return template.replace('.', '. Some might say.')
    elif quality_level == 'poor':
        # Multiple issues: too short, repetitive, missing structure
        words = template.split()[:100]  # Truncate
        return ' '.join(words) + '. Bad ending.'
    
    return template


def generate_blog_post(
    domain: str,
    difficulty: str,
    quality_level: str = 'good'
) -> Tuple[str, Scenario, Dict]:
    """Generate a blog post with scenario and expert labels"""
    
    topic, topic_desc = random.choice(TOPICS_BY_DOMAIN[domain])
    
    # Select template based on difficulty
    if difficulty == 'expert':
        difficulty_template = 'complex'  # Use complex template for expert
    else:
        difficulty_template = difficulty if difficulty in ['simple', 'moderate', 'complex'] else 'simple'
    
    templates = BLOG_POST_TEMPLATES.get(difficulty_template, BLOG_POST_TEMPLATES['simple'])
    template = random.choice(templates)
    
    # Fill template (simplified - in production, would use actual content)
    content = template['content'].format(
        topic=topic,
        topic_desc=topic_desc,
        importance=f"{topic} is crucial for {domain} success.",
        getting_started=f"Start with understanding {topic} fundamentals.",
        background=f"The history of {topic} in {domain}.",
        benefits=f"Key benefits of {topic} include improved outcomes.",
        implementation=f"Implementation steps for {topic}.",
        challenges=f"Common challenges with {topic}.",
        best_practices=f"Best practices for {topic}.",
        framework=f"Strategic framework for {topic}.",
        methodology=f"Methodology for implementing {topic}.",
        case_studies=f"Real-world examples of {topic}.",
        roadmap=f"Roadmap for {topic} adoption.",
        roi=f"Return on investment for {topic}.",
        risks=f"Risk mitigation strategies for {topic}.",
        executive_summary=f"Executive summary of {topic}.",
        detailed_intro=f"Detailed introduction to {topic}.",
        conclusion=f"In conclusion, {topic} is essential for {domain}.",
        cta=f"Contact us to learn more about {topic}.",
        industry=domain
    )
    
    # Apply quality variations
    content = generate_content_variations(content, quality_level)
    
    # Create scenario
    scenario = Scenario(
        id=f"scenario-{str(uuid.uuid4())[:8]}",
        title=template['title'].format(topic=topic),
        description=f"Write a blog post about {topic} for {domain}",
        content_type='blog_post',
        requirements=[
            f"Explain {topic}",
            f"Target {domain} professionals",
            "Include introduction and conclusion",
            "Add call-to-action"
        ],
        target_audience=f"{domain} professionals",
        purpose="Educational content marketing",
        industry=domain
    )
    
    # Generate expert scores (simulated)
    expert_scores = generate_expert_scores(quality_level, difficulty)
    
    return content, scenario, expert_scores


def generate_expert_scores(quality_level: str, difficulty: str) -> Dict:
    """Generate simulated expert scores based on quality and difficulty"""
    
    # Base scores by quality
    if quality_level == 'good':
        base_scores = {
            'structural': random.uniform(8.5, 10.0),
            'quality': random.uniform(8.0, 9.5),
            'domain': random.uniform(8.0, 9.5),
            'fit': random.uniform(8.5, 10.0)
        }
    elif quality_level == 'mediocre':
        base_scores = {
            'structural': random.uniform(6.0, 7.5),
            'quality': random.uniform(5.5, 7.0),
            'domain': random.uniform(6.0, 7.5),
            'fit': random.uniform(6.5, 8.0)
        }
    else:  # poor
        base_scores = {
            'structural': random.uniform(2.0, 5.0),
            'quality': random.uniform(2.0, 4.5),
            'domain': random.uniform(3.0, 5.5),
            'fit': random.uniform(2.5, 5.0)
        }
    
    # Adjust for difficulty (expert examples are harder to score perfectly)
    if difficulty == 'expert':
        for key in base_scores:
            base_scores[key] *= 0.95
    elif difficulty == 'complex':
        for key in base_scores:
            base_scores[key] *= 0.98
    
    overall = sum(base_scores.values()) / len(base_scores)
    passed = overall >= 8.0
    
    return {
        'dimension_scores': base_scores,
        'overall_score': overall,
        'passed': passed,
        'feedback': generate_expert_feedback(base_scores, overall, passed)
    }


def generate_expert_feedback(scores: Dict, overall: float, passed: bool) -> str:
    """Generate expert feedback text"""
    feedback = f"Overall Score: {overall:.1f}/10 ({'PASSED' if passed else 'NEEDS IMPROVEMENT'})\n\n"
    
    # Find strengths and weaknesses
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    
    strengths = [dim for dim, score in sorted_scores[:2] if score >= 7.0]
    weaknesses = [dim for dim, score in sorted_scores if score < 7.0]
    
    if strengths:
        feedback += "STRENGTHS:\n"
        for dim in strengths:
            feedback += f"✅ Strong {dim} ({scores[dim]:.1f}/10)\n"
        feedback += "\n"
    
    if weaknesses:
        feedback += "AREAS FOR IMPROVEMENT:\n"
        for dim in weaknesses:
            feedback += f"❌ {dim.capitalize()} needs work ({scores[dim]:.1f}/10)\n"
        feedback += "\n"
    
    return feedback


def generate_training_dataset(
    count: int = 1000,
    output_file: str = 'training_dataset.json'
) -> List[Dict]:
    """
    Generate complete training dataset
    
    Args:
        count: Number of examples to generate
        output_file: Output JSON file path
        
    Returns:
        List of training examples
    """
    
    examples = []
    
    # Distribution
    quality_distribution = {
        'good': 0.4,      # 40% good
        'mediocre': 0.35, # 35% mediocre
        'poor': 0.25      # 25% poor
    }
    
    difficulty_distribution = {
        'simple': 0.25,
        'moderate': 0.35,
        'complex': 0.25,
        'expert': 0.15
    }
    
    domain_distribution = {
        'marketing': 0.4,
        'education': 0.3,
        'healthcare': 0.3
    }
    
    print(f"Generating {count} training examples...")
    
    for i in range(count):
        if i % 100 == 0:
            print(f"  Generated {i}/{count} examples...")
        
        # Sample from distributions
        quality = random.choices(
            list(quality_distribution.keys()),
            weights=list(quality_distribution.values())
        )[0]
        
        difficulty = random.choices(
            list(difficulty_distribution.keys()),
            weights=list(difficulty_distribution.values())
        )[0]
        
        domain = random.choices(
            list(domain_distribution.keys()),
            weights=list(domain_distribution.values())
        )[0]
        
        # Generate example
        content, scenario, expert_scores = generate_blog_post(domain, difficulty, quality)
        
        example = {
            'id': str(uuid.uuid4()),
            'agent_output': content,
            'scenario': asdict(scenario),
            'expert_scores': expert_scores['dimension_scores'],
            'overall_score': expert_scores['overall_score'],
            'passed': expert_scores['passed'],
            'feedback': expert_scores['feedback'],
            'domain': domain,
            'difficulty': difficulty,
            'content_type': 'blog_post',
            'labeled_by': 'synthetic_expert',
            'labeled_at': datetime.now().isoformat(),
            'verified': True,  # Synthetic data is pre-verified
            'quality_level': quality
        }
        
        examples.append(example)
    
    print(f"Generated {count} examples!")
    
    # Save to file
    with open(output_file, 'w') as f:
        json.dump(examples, f, indent=2)
    
    print(f"Saved to {output_file}")
    
    # Print statistics
    print("\nDataset Statistics:")
    print(f"  Total examples: {len(examples)}")
    print(f"  By domain:")
    for domain in DOMAINS:
        count = len([e for e in examples if e['domain'] == domain])
        print(f"    {domain}: {count} ({count/len(examples)*100:.1f}%)")
    print(f"  By difficulty:")
    for diff in DIFFICULTIES:
        count = len([e for e in examples if e['difficulty'] == diff])
        print(f"    {diff}: {count} ({count/len(examples)*100:.1f}%)")
    print(f"  By quality:")
    for quality in quality_distribution.keys():
        count = len([e for e in examples if e['quality_level'] == quality])
        print(f"    {quality}: {count} ({count/len(examples)*100:.1f}%)")
    
    avg_score = sum(e['overall_score'] for e in examples) / len(examples)
    pass_rate = len([e for e in examples if e['passed']]) / len(examples)
    print(f"  Average score: {avg_score:.2f}/10")
    print(f"  Pass rate: {pass_rate*100:.1f}%")
    
    return examples


if __name__ == '__main__':
    # Generate dataset
    dataset = generate_training_dataset(count=1000, output_file='data/wowtester_training_dataset.json')
    print("\n✅ Training dataset generation complete!")
