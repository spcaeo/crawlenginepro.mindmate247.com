#!/usr/bin/env python3
"""
Metadata boosting using ALL 4 fields
- keywords: Exact keyword matching
- topics: Category relevance
- questions: Question similarity
- summary: Coverage check
"""

import re
from typing import List, Dict, Set, Tuple
from models import MetadataMatch

# ============================================================================
# Helper Functions
# ============================================================================

def extract_query_keywords(query: str) -> Set[str]:
    """
    Extract keywords from query (lowercase, remove stopwords)

    Args:
        query: User query text

    Returns:
        Set of cleaned keywords
    """
    # Common stopwords to filter out
    stopwords = {
        "the", "a", "an", "is", "are", "was", "were", "to", "of",
        "in", "on", "at", "by", "for", "with", "from", "what",
        "how", "why", "when", "where", "who", "which", "did", "do", "does"
    }

    # Extract words (alphanumeric only)
    words = re.findall(r'\w+', query.lower())

    # Filter out stopwords and short words
    return set(w for w in words if w not in stopwords and len(w) > 2)

# ============================================================================
# Boost Functions (One per Metadata Field)
# ============================================================================

def boost_keywords(query_keywords: Set[str], chunk_keywords: str, weight: float) -> Tuple[float, List[str]]:
    """
    Boost score based on keyword matches

    Args:
        query_keywords: Set of keywords extracted from query
        chunk_keywords: Comma-separated keywords from chunk metadata
        weight: Boost weight per match

    Returns:
        (boost_score, matched_keywords)
    """
    if not chunk_keywords:
        return 0.0, []

    # Parse chunk keywords (comma-separated)
    chunk_kw = set(kw.strip().lower() for kw in chunk_keywords.split(",") if kw.strip())

    # Find matches
    matches = query_keywords.intersection(chunk_kw)

    # +weight per match, max 3 matches counted (diminishing returns)
    boost = min(len(matches), 3) * weight

    return boost, list(matches)

def boost_topics(query_keywords: Set[str], chunk_topics: str, weight: float) -> Tuple[float, List[str]]:
    """
    Boost score based on topic relevance

    Args:
        query_keywords: Set of keywords extracted from query
        chunk_topics: Comma-separated topics from chunk metadata
        weight: Boost weight per match

    Returns:
        (boost_score, matched_topics)
    """
    if not chunk_topics:
        return 0.0, []

    # Parse topics (comma-separated)
    topics = [t.strip().lower() for t in chunk_topics.split(",") if t.strip()]
    matches = []

    # Check if any query keyword appears in topic
    for topic in topics:
        topic_words = set(re.findall(r'\w+', topic))
        if query_keywords.intersection(topic_words):
            matches.append(topic)

    # +weight per matching topic
    boost = len(matches) * weight

    return boost, matches

def boost_questions(query: str, chunk_questions: str, weight: float) -> float:
    """
    Boost score if chunk question matches query intent
    Uses simple word overlap (can upgrade to semantic similarity later)

    Args:
        query: Original query text
        chunk_questions: Question marks separated questions from chunk metadata
        weight: Boost weight for similarity

    Returns:
        boost_score
    """
    if not chunk_questions:
        return 0.0

    # Extract query keywords
    query_words = extract_query_keywords(query)

    # Split questions by '?' and clean
    questions = [q.strip().lower() for q in chunk_questions.split("?") if q.strip()]

    # Calculate max similarity across all questions
    max_similarity = 0.0
    for question in questions:
        q_words = set(re.findall(r'\w+', question))
        if q_words:
            # Jaccard similarity
            overlap = len(query_words.intersection(q_words)) / len(query_words.union(q_words))
            max_similarity = max(max_similarity, overlap)

    # High similarity gets full weight
    if max_similarity > 0.5:
        return weight
    elif max_similarity > 0.3:
        return weight * 0.5
    else:
        return 0.0

def boost_summary(query_keywords: Set[str], chunk_summary: str, weight: float) -> float:
    """
    Boost score based on summary keyword coverage

    Args:
        query_keywords: Set of keywords extracted from query
        chunk_summary: Summary text from chunk metadata
        weight: Boost weight for coverage

    Returns:
        boost_score
    """
    if not chunk_summary:
        return 0.0

    # Extract words from summary
    summary_words = set(re.findall(r'\w+', chunk_summary.lower()))

    # Calculate coverage (how many query keywords appear in summary)
    if not query_keywords:
        return 0.0

    coverage = len(query_keywords.intersection(summary_words)) / len(query_keywords)

    # High coverage gets full weight
    if coverage > 0.6:
        return weight
    elif coverage > 0.3:
        return weight * (coverage / 0.6)
    else:
        return 0.0

# ============================================================================
# Main Boosting Function
# ============================================================================

def apply_metadata_boost(
    query: str,
    chunk: Dict,
    weights: Dict[str, float],
    max_boost: float = 0.30
) -> Tuple[float, MetadataMatch]:
    """
    Apply ALL 4 metadata field boosts

    Args:
        query: User query text
        chunk: Chunk dictionary with metadata fields
        weights: Boost weights for each field
        max_boost: Maximum total boost allowed

    Returns:
        (total_boost, metadata_match_details)
    """
    # Extract query keywords once
    query_kw = extract_query_keywords(query)

    # Boost from each field
    kw_boost, kw_matches = boost_keywords(
        query_kw,
        chunk.get("keywords", ""),
        weights.get("keywords", 0.10)
    )

    topic_boost, topic_matches = boost_topics(
        query_kw,
        chunk.get("topics", ""),
        weights.get("topics", 0.05)
    )

    question_boost = boost_questions(
        query,
        chunk.get("questions", ""),
        weights.get("questions", 0.08)
    )

    summary_boost = boost_summary(
        query_kw,
        chunk.get("summary", ""),
        weights.get("summary", 0.07)
    )

    # Calculate normalized scores (0-1) for reporting
    question_weight = weights.get("questions", 0.08)
    question_sim = (question_boost / question_weight) if question_weight > 0 else 0.0

    summary_weight = weights.get("summary", 0.07)
    summary_cov = (summary_boost / summary_weight) if summary_weight > 0 else 0.0

    # Total boost (capped at max_boost)
    total_boost = min(kw_boost + topic_boost + question_boost + summary_boost, max_boost)

    # Build metadata match details
    metadata_match = MetadataMatch(
        keywords_matched=kw_matches,
        topics_matched=topic_matches,
        question_similarity=question_sim,
        summary_coverage=summary_cov
    )

    return total_boost, metadata_match
