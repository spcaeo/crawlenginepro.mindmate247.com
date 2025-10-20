#!/usr/bin/env python3
"""
Comprehensive Metadata Quality Audit
Analyzes the 7 metadata fields for accuracy, completeness, and duplication
"""

from pymilvus import connections, Collection
import json

# Connect to Milvus
connections.connect(host="localhost", port="19530")
collection = Collection("test_comprehensive_v4")
collection.load()

# Query all chunks
results = collection.query(
    expr="chunk_index >= 0",
    output_fields=["id", "text", "keywords", "topics", "questions", "summary",
                   "semantic_keywords", "entity_relationships", "attributes"],
    limit=20
)

print("=" * 100)
print("METADATA QUALITY AUDIT REPORT")
print("=" * 100)
print(f"\nTotal chunks analyzed: {len(results)}\n")

# Analyze each chunk
issues_found = []
for i, chunk in enumerate(results[:5], 1):  # Detailed analysis of first 5 chunks
    print(f"\n{'=' * 100}")
    print(f"CHUNK {i}: {chunk['id']}")
    print(f"{'=' * 100}")

    text = chunk['text']
    print(f"\n📄 SOURCE TEXT ({len(text)} chars):")
    print(f"{text[:300]}..." if len(text) > 300 else text)

    print(f"\n📊 METADATA FIELDS:\n")

    # 1. Keywords
    keywords = chunk.get('keywords', '')
    print(f"1️⃣  KEYWORDS: {keywords}")
    if keywords:
        kw_list = [k.strip() for k in keywords.split(',')]
        print(f"   Count: {len(kw_list)} keywords")

        # Check if keywords actually appear in text
        text_lower = text.lower()
        not_in_text = [kw for kw in kw_list if kw.lower() not in text_lower and len(kw) > 3]
        if not_in_text:
            issue = f"Chunk {i}: Keywords not in text: {not_in_text[:3]}"
            issues_found.append(issue)
            print(f"   ⚠️  Keywords NOT in text: {not_in_text[:3]}")
    else:
        issues_found.append(f"Chunk {i}: EMPTY keywords")
        print("   ❌ EMPTY")

    # 2. Topics
    topics = chunk.get('topics', '')
    print(f"\n2️⃣  TOPICS: {topics}")
    if not topics:
        issues_found.append(f"Chunk {i}: EMPTY topics")
        print("   ❌ EMPTY")

    # 3. Questions
    questions = chunk.get('questions', '')
    print(f"\n3️⃣  QUESTIONS: {questions}")
    if questions:
        q_list = [q.strip() for q in questions.split('|')]
        print(f"   Count: {len(q_list)} questions")
    else:
        issues_found.append(f"Chunk {i}: EMPTY questions")
        print("   ❌ EMPTY")

    # 4. Summary
    summary = chunk.get('summary', '')
    print(f"\n4️⃣  SUMMARY: {summary}")
    if not summary:
        issues_found.append(f"Chunk {i}: EMPTY summary")
        print("   ❌ EMPTY")

    # 5. Semantic Keywords
    sem_kw = chunk.get('semantic_keywords', '')
    print(f"\n5️⃣  SEMANTIC_KEYWORDS: {sem_kw}")
    if sem_kw:
        sem_list = [k.strip() for k in sem_kw.split(',')]
        print(f"   Count: {len(sem_list)} semantic keywords")

        # Check for duplication with keywords
        if keywords:
            kw_set = set([k.strip().lower() for k in keywords.split(',')])
            sem_set = set([k.strip().lower() for k in sem_kw.split(',')])
            duplicates = kw_set.intersection(sem_set)
            if duplicates:
                print(f"   ⚠️  DUPLICATES with keywords: {list(duplicates)[:3]}")
                issues_found.append(f"Chunk {i}: Semantic keywords duplicate main keywords: {list(duplicates)[:3]}")
    else:
        issues_found.append(f"Chunk {i}: EMPTY semantic_keywords")
        print("   ❌ EMPTY")

    # 6. Entity Relationships
    ent_rel = chunk.get('entity_relationships', '')
    print(f"\n6️⃣  ENTITY_RELATIONSHIPS: {ent_rel}")
    if ent_rel:
        rel_list = [r.strip() for r in ent_rel.split('|')]
        print(f"   Count: {len(rel_list)} relationships")

        # Parse relationships
        for rel in rel_list[:3]:
            if '→' in rel:
                parts = rel.split('→')
                if len(parts) == 3:
                    print(f"      • {parts[0].strip()} --[{parts[1].strip()}]--> {parts[2].strip()}")
    else:
        issues_found.append(f"Chunk {i}: EMPTY entity_relationships")
        print("   ❌ EMPTY")

    # 7. Attributes
    attrs = chunk.get('attributes', '')
    print(f"\n7️⃣  ATTRIBUTES: {attrs}")
    if attrs:
        attr_list = [a.strip() for a in attrs.split(',')]
        print(f"   Count: {len(attr_list)} key-value pairs")

        # Parse key-value pairs
        for attr in attr_list[:5]:
            if ':' in attr:
                key, val = attr.split(':', 1)
                print(f"      • {key.strip()}: {val.strip()}")
    else:
        issues_found.append(f"Chunk {i}: EMPTY attributes")
        print("   ❌ EMPTY")

# Overall statistics
print(f"\n\n{'=' * 100}")
print("OVERALL STATISTICS")
print(f"{'=' * 100}\n")

empty_counts = {
    'keywords': 0,
    'topics': 0,
    'questions': 0,
    'summary': 0,
    'semantic_keywords': 0,
    'entity_relationships': 0,
    'attributes': 0
}

for chunk in results:
    for field in empty_counts.keys():
        if not chunk.get(field, ''):
            empty_counts[field] += 1

print("Empty Field Statistics:")
for field, count in empty_counts.items():
    percentage = (count / len(results)) * 100
    status = "✅" if count == 0 else ("⚠️ " if count < len(results) * 0.3 else "❌")
    print(f"  {status} {field:25s}: {count:2d}/{len(results)} empty ({percentage:5.1f}%)")

print(f"\n\nISSUES FOUND ({len(issues_found)} total):")
for issue in issues_found[:10]:
    print(f"  ⚠️  {issue}")

if len(issues_found) > 10:
    print(f"  ... and {len(issues_found) - 10} more issues")

# Recommendations
print(f"\n\n{'=' * 100}")
print("RECOMMENDATIONS")
print(f"{'=' * 100}\n")

if empty_counts['semantic_keywords'] > 0:
    print("❌ CRITICAL: semantic_keywords field is empty in some chunks")
    print("   → Check if metadata service is actually generating this field")
    print("   → Verify storage service is accepting and storing this field")

if empty_counts['entity_relationships'] > 0:
    print("\n❌ CRITICAL: entity_relationships field is empty in some chunks")
    print("   → Verify LLM prompt is requesting relationship extraction")
    print("   → Check if storage service model includes this field")

if empty_counts['attributes'] > 0:
    print("\n❌ CRITICAL: attributes field is empty in some chunks")
    print("   → Verify LLM prompt is requesting key-value attributes")
    print("   → Check field mapping in storage pipeline")

# Check for duplicates
print("\n💡 Quality Improvements:")
print("   1. Semantic keywords should be DIFFERENT from main keywords (synonyms, expansions)")
print("   2. Entity relationships should follow format: Entity1 → relationship → Entity2")
print("   3. Attributes should be structured as key:value pairs for filtering")
print("   4. Keywords should focus on EXACT terms from text (full names, SKUs, dates)")

connections.disconnect("default")
