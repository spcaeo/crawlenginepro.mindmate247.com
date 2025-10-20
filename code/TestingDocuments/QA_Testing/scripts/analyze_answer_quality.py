#!/usr/bin/env python3
"""
Answer Quality Analysis Script
Provides deep analysis comparing expected vs actual answers

Usage:
  python analyze_answer_quality.py <test_id>
  python analyze_answer_quality.py 1.1

Author: CrawlEnginePro
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any

# ANSI color codes
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

# Expected answers for each query (from Q&A.md)
EXPECTED_ANSWERS = {
    "1.1": {
        "question": "Compare the technical terms used in the Nike Air Zoom Pegasus 40 and Michelin Pilot Sport 4S Tire sections; what technologies do they share?",
        "expected_answer": """
- Nike Air Zoom Pegasus 40 technical terms: React foam technology, Zoom Air cushioning, engineered mesh, waffle-pattern traction
- Michelin Pilot Sport 4S Tire technical terms: Bi-compound technology, Dynamic Response Technology, Variable Contact Patch 3.0, Hybrid Aramid/Nylon belt package
- Shared/Similar Technologies: Both emphasize advanced material science for performance—Nike uses engineered mesh for breathability and traction, while Michelin uses bi-compound tread and hybrid belt for grip and handling. No direct overlap in proprietary technologies, but both focus on comfort, traction, and responsiveness.
        """.strip(),
        "difficulty": "hard",
        "reason": "Requires synthesizing technical terminology across unrelated product categories and identifying thematic similarities rather than exact matches.",
        "expected_rag_behavior": "Most systems will return isolated details about Nike or Michelin separately, listing technical terms from each section but not synthesizing similarities. They'll likely miss nuanced links like shared emphasis on 'traction' or 'performance' unless explicitly connected in text.",
        "capability": "cross-domain synthesis"
    },
    "1.2": {
        "question": "Which vendors appear in both technology and medical equipment invoices, and what are their order statuses?",
        "expected_answer": """
- Technology invoice vendor: TechSupply Solutions
- Medical equipment invoice vendor: MedTech Equipment Supply
- Order statuses: Technology (Paid); Medical Equipment (Net 30 - Due 2024-03-30)
- Overlap: There is no vendor appearing in both invoices, and each order has its own distinct status
        """.strip(),
        "difficulty": "hard",
        "reason": "Requires checking multiple invoice sections, comparing vendor lists, and accurately reporting absence of overlap.",
        "expected_rag_behavior": "Most systems will list vendors and statuses for each invoice section but generally do not detect or report absence of overlap unless it's stated directly.",
        "capability": "negative assertion"
    },
    "1.3": {
        "question": "Find the highest-priced product listed across all invoices and describe its key features and technical specifications.",
        "expected_answer": """
- The highest-priced product is the Hobart Commercial Dishwasher (Model LXeR-2) at $8,999.00 USD
- Key features and technical specifications: High-temperature sanitizing, 40 racks/hour capacity, Energy Star certified, chemical/solid waste pumping system, dimensions 24.5 x 25 x 34 inches
        """.strip(),
        "difficulty": "medium",
        "reason": "Requires aggregating prices across all invoices, ranking them, then retrieving associated specifications in a single integrated response.",
        "expected_rag_behavior": "Typical systems may focus on price extraction but miss relating features/specs in a single, concise response. May not rank all products across invoices unless one query retrieves all prices and another the associated features.",
        "capability": "aggregation and ranking"
    },
    # Add more expected answers as needed
}

def load_latest_result(test_id: str) -> Dict[str, Any]:
    """Load the most recent test result for a given test ID"""
    results_dir = Path(__file__).parent.parent / "results"

    # Find all result files
    result_files = sorted(results_dir.glob("qa_test_results_*.json"), reverse=True)

    for result_file in result_files:
        with open(result_file, 'r') as f:
            data = json.load(f)

        # Find the test result
        for test in data.get('test_results', []):
            if test.get('test_id') == test_id:
                return test

    return None

def analyze_answer(test_id: str, actual_result: Dict[str, Any]) -> None:
    """Perform deep analysis of answer quality"""

    if test_id not in EXPECTED_ANSWERS:
        print(f"{Colors.FAIL}❌ No expected answer defined for test {test_id}{Colors.ENDC}")
        return

    expected = EXPECTED_ANSWERS[test_id]
    actual_answer = actual_result.get('answer', '')

    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*100}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}COMPREHENSIVE ANSWER ANALYSIS - Query {test_id}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*100}{Colors.ENDC}\n")

    # 1. Test Configuration
    print(f"{Colors.BOLD}📋 TEST CONFIGURATION{Colors.ENDC}")
    print(f"  Query ID: {test_id}")
    print(f"  Difficulty: {expected['difficulty']}")
    print(f"  Capability: {expected['capability']}")
    print(f"  Category: {actual_result.get('category', 'unknown')}")

    # 2. Performance Summary
    print(f"\n{Colors.BOLD}⏱️  PERFORMANCE SUMMARY{Colors.ENDC}")
    perf = actual_result.get('performance', {})
    print(f"  Total Time: {perf.get('total_time_ms', 0):.0f}ms ({perf.get('total_time_ms', 0)/1000:.2f}s)")
    print(f"  Server Time: {perf.get('server_time_ms', 0):.0f}ms")

    stage_times = perf.get('stage_times', {})
    print(f"\n  Pipeline Breakdown:")
    print(f"    Intent Detection: {stage_times.get('intent_detection_ms', 0):.0f}ms")
    print(f"    Search: {stage_times.get('search_ms', 0):.0f}ms")
    print(f"    Reranking: {stage_times.get('reranking_ms', 0):.0f}ms")
    print(f"    Compression: {stage_times.get('compression_ms', 0):.0f}ms")
    print(f"    Answer Generation: {stage_times.get('answer_generation_ms', 0):.0f}ms")

    bottleneck = perf.get('bottleneck', {})
    print(f"\n  🔴 Bottleneck: {bottleneck.get('stage', 'unknown')} ({bottleneck.get('time_ms', 0):.0f}ms = {bottleneck.get('percentage_of_total', 0):.1f}%)")

    # 3. Intent & Model Analysis
    print(f"\n{Colors.BOLD}🧠 INTENT & MODEL ANALYSIS{Colors.ENDC}")
    intent = actual_result.get('intent_analysis', {})
    models = actual_result.get('models_used', {})

    print(f"  Detected Intent: {intent.get('detected_intent', 'unknown')}")
    print(f"  Confidence: {intent.get('confidence', 0)*100:.1f}%")
    print(f"  Language: {intent.get('language', 'unknown')}")
    print(f"  Complexity: {intent.get('complexity', 'unknown')}")
    print(f"  Recommended Model: {intent.get('recommended_model', 'unknown')}")
    print(f"  Model Actually Used: {models.get('llm_used', 'unknown')}")
    print(f"  Used Recommended: {'✅ Yes' if models.get('used_recommended_model') else '❌ No'}")
    print(f"  Custom Prompt: {'✅ Yes' if models.get('used_custom_prompt') else '❌ No'}")

    # 4. Keyword Coverage
    print(f"\n{Colors.BOLD}✅ KEYWORD COVERAGE{Colors.ENDC}")
    kw_analysis = actual_result.get('keyword_analysis', {})
    coverage = kw_analysis.get('coverage_percentage', 0)

    print(f"  Coverage: {coverage:.1f}%")
    print(f"  Expected Keywords: {len(kw_analysis.get('expected_keywords', []))}")
    print(f"  Keywords Found: {len(kw_analysis.get('keywords_found', []))}")

    if kw_analysis.get('keywords_found'):
        print(f"\n  ✅ Found Keywords:")
        for kw in kw_analysis.get('keywords_found', []):
            print(f"    • {kw}")

    if kw_analysis.get('keywords_missing'):
        print(f"\n  ❌ Missing Keywords:")
        for kw in kw_analysis.get('keywords_missing', []):
            print(f"    • {kw}")

    # 5. Expected vs Actual Answer Comparison
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*100}{Colors.ENDC}")
    print(f"{Colors.BOLD}📊 EXPECTED vs ACTUAL ANSWER COMPARISON{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*100}{Colors.ENDC}\n")

    print(f"{Colors.OKCYAN}EXPECTED ANSWER:{Colors.ENDC}")
    print(expected['expected_answer'])

    print(f"\n{Colors.OKGREEN}ACTUAL ANSWER:{Colors.ENDC}")
    print(actual_answer[:2000])  # Limit to first 2000 chars for readability
    if len(actual_answer) > 2000:
        print(f"\n... (truncated, full answer in results file)")

    # 6. Test Difficulty & Challenge
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*100}{Colors.ENDC}")
    print(f"{Colors.BOLD}🎯 TEST CHALLENGE ANALYSIS{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*100}{Colors.ENDC}\n")

    print(f"{Colors.WARNING}Why This Query is Difficult:{Colors.ENDC}")
    print(f"  {expected['reason']}")

    print(f"\n{Colors.WARNING}Expected RAG System Behavior:{Colors.ENDC}")
    print(f"  {expected['expected_rag_behavior']}")

    # 7. Quality Assessment
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*100}{Colors.ENDC}")
    print(f"{Colors.BOLD}⭐ QUALITY ASSESSMENT{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*100}{Colors.ENDC}\n")

    # Simple heuristic scoring
    score = 0
    max_score = 5

    # Keyword coverage
    if coverage >= 100:
        score += 1
        print(f"  ✅ Keyword Coverage: EXCELLENT (100%)")
    elif coverage >= 80:
        score += 0.8
        print(f"  ✅ Keyword Coverage: GOOD ({coverage:.1f}%)")
    elif coverage >= 60:
        score += 0.6
        print(f"  ⚠️  Keyword Coverage: FAIR ({coverage:.1f}%)")
    else:
        print(f"  ❌ Keyword Coverage: POOR ({coverage:.1f}%)")

    # Answer length (should have substantial content)
    if len(actual_answer) > 500:
        score += 1
        print(f"  ✅ Answer Depth: COMPREHENSIVE ({len(actual_answer)} chars)")
    elif len(actual_answer) > 200:
        score += 0.7
        print(f"  ✅ Answer Depth: ADEQUATE ({len(actual_answer)} chars)")
    else:
        print(f"  ❌ Answer Depth: TOO SHORT ({len(actual_answer)} chars)")

    # Model selection
    if models.get('used_recommended_model'):
        score += 1
        print(f"  ✅ Model Selection: OPTIMAL (used recommended model)")
    else:
        score += 0.5
        print(f"  ⚠️  Model Selection: SUBOPTIMAL (did not use recommended model)")

    # Custom prompting
    if models.get('used_custom_prompt'):
        score += 1
        print(f"  ✅ Custom Prompting: YES (intent-specific prompt)")
    else:
        print(f"  ❌ Custom Prompting: NO (generic prompt)")

    # Performance
    total_time = perf.get('total_time_ms', 0)
    if total_time < 4000:
        score += 1
        print(f"  ✅ Performance: EXCELLENT ({total_time:.0f}ms < 4s)")
    elif total_time < 7000:
        score += 0.7
        print(f"  ✅ Performance: GOOD ({total_time:.0f}ms < 7s)")
    else:
        score += 0.5
        print(f"  ⚠️  Performance: SLOW ({total_time:.0f}ms)")

    # Final score
    print(f"\n{Colors.BOLD}Overall Quality Score: {score:.1f}/{max_score} ({'⭐' * int(score)}){Colors.ENDC}")

    if score >= 4.5:
        print(f"{Colors.OKGREEN}  Rating: EXCELLENT ⭐⭐⭐⭐⭐{Colors.ENDC}")
    elif score >= 3.5:
        print(f"{Colors.OKGREEN}  Rating: VERY GOOD ⭐⭐⭐⭐{Colors.ENDC}")
    elif score >= 2.5:
        print(f"{Colors.WARNING}  Rating: GOOD ⭐⭐⭐{Colors.ENDC}")
    elif score >= 1.5:
        print(f"{Colors.WARNING}  Rating: FAIR ⭐⭐{Colors.ENDC}")
    else:
        print(f"{Colors.FAIL}  Rating: NEEDS IMPROVEMENT ⭐{Colors.ENDC}")

    # 8. Retrieval Quality
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*100}{Colors.ENDC}")
    print(f"{Colors.BOLD}🔍 RETRIEVAL QUALITY{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*100}{Colors.ENDC}\n")

    retrieval = actual_result.get('retrieval_metrics', {})
    print(f"  Search Results: {retrieval.get('search_results_count', 0)} chunks")
    print(f"  After Reranking: {retrieval.get('reranked_count', 0)} chunks")
    print(f"  After Compression: {retrieval.get('compressed_count', 0)} chunks")
    print(f"  Used in Context: {retrieval.get('context_count', 0)} chunks")
    print(f"  Citations: {actual_result.get('citations_count', 0)}")

    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*100}{Colors.ENDC}")
    print(f"{Colors.OKGREEN}✅ Analysis Complete!{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*100}{Colors.ENDC}\n")

def main():
    if len(sys.argv) < 2:
        print(f"{Colors.FAIL}Usage: python analyze_answer_quality.py <test_id>{Colors.ENDC}")
        print(f"Example: python analyze_answer_quality.py 1.1")
        sys.exit(1)

    test_id = sys.argv[1]

    print(f"\n{Colors.BOLD}Loading test result for Query {test_id}...{Colors.ENDC}")
    result = load_latest_result(test_id)

    if not result:
        print(f"{Colors.FAIL}❌ No test result found for Query {test_id}{Colors.ENDC}")
        print(f"{Colors.WARNING}Please run the test first: python run_qa_tests.py {test_id}{Colors.ENDC}")
        sys.exit(1)

    if not result.get('success'):
        print(f"{Colors.FAIL}❌ Test {test_id} failed: {result.get('error')}{Colors.ENDC}")
        sys.exit(1)

    analyze_answer(test_id, result)

if __name__ == "__main__":
    main()
