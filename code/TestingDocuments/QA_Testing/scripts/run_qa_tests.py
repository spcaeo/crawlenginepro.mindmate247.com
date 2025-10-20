#!/usr/bin/env python3
"""
Q&A Retrieval Testing Script
Tests retrieval pipeline with comprehensive question set
Tracks performance metrics and saves results in JSON format

Usage:
  python run_qa_tests.py           # Run all 18 tests
  python run_qa_tests.py 1.1       # Run only Query 1.1
  python run_qa_tests.py 1.1 1.2   # Run Query 1.1 and 1.2

Author: CrawlEnginePro
"""

import json
import time
import requests
import sys
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

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

# Configuration
RETRIEVAL_API_URL = "http://localhost:8090/v1/retrieve"
COLLECTION_NAME = "test_comprehensive_v4"  # Updated for enhanced metadata testing
TENANT_ID = "test_tenant"  # Updated for enhanced metadata testing
RESULTS_DIR = Path(__file__).parent.parent / "results"
REPORTS_DIR = Path(__file__).parent.parent / "reports"

# Ensure directories exist
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Test Questions (18 questions across 7 categories)
TEST_QUESTIONS = [
    # Category 1: Cross-Section Synthesis Queries
    {
        "id": "1.1",
        "category": "Cross-Section Synthesis",
        "question": "Compare the technical terms used in the Nike Air Zoom Pegasus 40 and Michelin Pilot Sport 4S Tire sections; what technologies do they share?",
        "expected_answer_keywords": ["React foam", "Zoom Air", "engineered mesh", "bi-compound", "traction", "performance"],
        "difficulty": "hard",
        "test_capability": "cross-domain synthesis"
    },
    {
        "id": "1.2",
        "category": "Cross-Section Synthesis",
        "question": "Which vendors appear in both technology and medical equipment invoices, and what are their order statuses?",
        "expected_answer_keywords": ["TechSupply Solutions", "MedTech Equipment Supply", "no overlap", "distinct"],
        "difficulty": "hard",
        "test_capability": "negative assertion"
    },
    {
        "id": "1.3",
        "category": "Cross-Section Synthesis",
        "question": "Find the highest-priced product listed across all invoices and describe its key features and technical specifications.",
        "expected_answer_keywords": ["Hobart", "Dishwasher", "$8,999", "sanitizing", "40 racks/hour", "Energy Star"],
        "difficulty": "medium",
        "test_capability": "aggregation and ranking"
    },

    # Category 2: Negative/Not-Found Testing
    {
        "id": "2.1",
        "category": "Negative/Not-Found Testing",
        "question": "What is the refund policy for any of the vendors listed?",
        "expected_answer_keywords": ["not found", "no information", "not specified", "unavailable"],
        "difficulty": "medium",
        "test_capability": "hallucination detection"
    },

    # Category 3: Standard Ecommerce Queries
    {
        "id": "3.1",
        "category": "Standard Ecommerce",
        "question": "What is the price and key specifications of the Apple iPhone 15 Pro Max listed in the catalog?",
        "expected_answer_keywords": ["$1,199", "A17 Pro", "256GB", "48MP", "titanium"],
        "difficulty": "easy",
        "test_capability": "basic retrieval"
    },
    {
        "id": "3.2",
        "category": "Standard Ecommerce",
        "question": "If I buy both the Apple iPhone 15 Pro Max and the Nike Air Zoom Pegasus 40 together, what is the combined shipping weight, and will the vendor provide a bundled warranty for both items?",
        "expected_answer_keywords": ["221 grams", "283 grams", "504 grams", "no bundled", "not specified"],
        "difficulty": "medium",
        "test_capability": "arithmetic and gap acknowledgment"
    },

    # Category 4: Certification and Compliance
    {
        "id": "4.1",
        "category": "Certification & Compliance",
        "question": "Which products in the catalog are certified by third-party organizations, and which organizations are involved in their certification?",
        "expected_answer_keywords": ["CardioHealth", "FDA-registered", "NSF International", "USP Verified"],
        "difficulty": "easy",
        "test_capability": "certification extraction"
    },
    {
        "id": "4.2",
        "category": "Certification & Compliance",
        "question": "Who is the institutional partner for the book titled 'The Future of Artificial Intelligence' and what is the publisher's distribution partner?",
        "expected_answer_keywords": ["Stanford AI Lab", "MIT Press"],
        "difficulty": "easy",
        "test_capability": "entity role disambiguation"
    },

    # Category 5: Temporal and Date-Based Reasoning
    {
        "id": "5.1",
        "category": "Temporal Reasoning",
        "question": "Which products have any information about expiration or best-before dates, and what are those dates?",
        "expected_answer_keywords": ["CardioHealth", "2024-01-15", "2026-12-31", "expiration", "best before"],
        "difficulty": "easy",
        "test_capability": "temporal information extraction"
    },
    {
        "id": "5.2",
        "category": "Temporal Reasoning",
        "question": "For any invoice with net payment terms, what is the due date and current payment status?",
        "expected_answer_keywords": ["Medical Equipment", "Net 30", "2024-03-30", "Construction", "2024-04-09"],
        "difficulty": "medium",
        "test_capability": "conditional filtering"
    },

    # Category 6: Multi-Category Comparison
    {
        "id": "6.1",
        "category": "Multi-Category Comparison",
        "question": "List and compare all the food-service equipment ordered for a restaurant, including main technical specs and purchase prices.",
        "expected_answer_keywords": ["Hobart", "Dishwasher", "$8,999", "Vulcan", "Gas Range", "$5,499", "True", "Refrigerator", "$3,299"],
        "difficulty": "medium",
        "test_capability": "categorical grouping"
    },

    # Category 7: Advanced Logical Reasoning
    {
        "id": "7.1",
        "category": "Advanced Logic",
        "question": "Which product listed in any invoice is not paid, and which vendor is responsible for it?",
        "expected_answer_keywords": ["Construction Materials", "BuildRight", "Pending", "2024-04-09", "not paid"],
        "difficulty": "hard",
        "test_capability": "negative logic"
    },
    {
        "id": "7.2",
        "category": "Advanced Logic",
        "question": "What is the total combined weight of one True Refrigerator and two Air Zoom Pegasus 40 shoes, in kilograms?",
        "expected_answer_keywords": ["283 grams", "566 grams", "0.566 kg", "refrigerator weight not specified"],
        "difficulty": "hard",
        "test_capability": "arithmetic and unit conversion"
    },
    {
        "id": "7.3",
        "category": "Advanced Logic",
        "question": "If the construction materials order is delayed by 30 days past its due date, which other invoice will then have a later due date?",
        "expected_answer_keywords": ["2024-04-09", "2024-05-09", "30-day delay", "latest due date"],
        "difficulty": "hard",
        "test_capability": "hypothetical scenario"
    },
    {
        "id": "7.4",
        "category": "Advanced Logic",
        "question": "For each product with a warranty, list the warranty term and identify the next related service (e.g., repair, return) process outlined—if any.",
        "expected_answer_keywords": ["no warranty", "not described", "not found", "not specified"],
        "difficulty": "hard",
        "test_capability": "multi-hop reasoning"
    },
    {
        "id": "7.5",
        "category": "Advanced Logic",
        "question": "Which items ordered from a vendor with 'Tech' in their company name require delivery outside of the technology category?",
        "expected_answer_keywords": ["MedTech", "Philips IntelliVue", "Welch Allyn", "Nonin", "medical equipment"],
        "difficulty": "hard",
        "test_capability": "fuzzy matching with constraints"
    },
    {
        "id": "7.6",
        "category": "Advanced Logic",
        "question": "Provide the payment terms explanation in both French and English for any invoice involving international shipment.",
        "expected_answer_keywords": ["no payment terms", "not specified", "no international shipment"],
        "difficulty": "hard",
        "test_capability": "conditional multi-language"
    },
    {
        "id": "7.7",
        "category": "Advanced Logic",
        "question": "List all products whose manufacturer is not the same as the listed vendor—and summarize each instance briefly.",
        "expected_answer_keywords": ["Dell XPS", "TechSupply", "Michelin", "Philips", "VitaLife", "Hobart", "third-party vendors"],
        "difficulty": "hard",
        "test_capability": "relationship graph understanding"
    }
]

def check_api_health():
    """Check if retrieval API is running"""
    try:
        response = requests.get("http://localhost:8090/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            return True, health_data
        return False, None
    except Exception as e:
        return False, str(e)

def get_service_models_and_cache():
    """Get model information and cache status from all services"""
    services_info = {}

    # Check embeddings service
    try:
        resp = requests.get("http://localhost:8073/health", timeout=3)
        if resp.status_code == 200:
            data = resp.json()
            services_info["embeddings"] = {
                "model": data.get("model"),
                "dimension": data.get("dense_dimension"),
                "provider": data.get("source"),
                "device": data.get("device"),
                "cache_enabled": data.get("cache_enabled", False),
                "cache_entries": data.get("cache_entries", 0)
            }
    except:
        services_info["embeddings"] = {"error": "unavailable"}

    # Check answer generation service
    try:
        resp = requests.get("http://localhost:8094/health", timeout=3)
        if resp.status_code == 200:
            data = resp.json()
            services_info["answer_generation"] = {
                "cache_enabled": data.get("dependencies", {}).get("cache", False)
            }
    except:
        services_info["answer_generation"] = {"error": "unavailable"}

    # Check reranking service
    try:
        resp = requests.get("http://localhost:8092/health", timeout=3)
        if resp.status_code == 200:
            data = resp.json()
            services_info["reranking"] = {
                "model": data.get("model"),
                "provider": data.get("device")
            }
    except:
        services_info["reranking"] = {"error": "unavailable"}

    return services_info

def run_single_query(question_data: Dict[str, Any], test_index: int, total_tests: int, response_style: Optional[str] = None) -> Dict[str, Any]:
    """Run a single Q&A test and return results

    Args:
        question_data: Question data dictionary
        test_index: Current test index
        total_tests: Total number of tests
        response_style: Optional override for answer style (concise/balanced/comprehensive)
    """

    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*100}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}Test {test_index}/{total_tests}: {question_data['id']} - {question_data['category']}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*100}{Colors.ENDC}")

    print(f"\n{Colors.OKCYAN}Question:{Colors.ENDC} {question_data['question']}")
    print(f"{Colors.OKBLUE}Difficulty:{Colors.ENDC} {question_data['difficulty']}")
    print(f"{Colors.OKBLUE}Test Capability:{Colors.ENDC} {question_data['test_capability']}")
    if response_style:
        print(f"{Colors.OKBLUE}Response Style:{Colors.ENDC} {response_style.upper()} (override)\n")
    else:
        print()

    # Prepare request payload
    # Note: "model" field is optional - it will use the recommended model from Intent Service
    # If no recommendation, it falls back to the default in models.py

    # Adjust rerank_top_k based on query difficulty
    # Aggregation/ranking/cross-reference queries need more chunks for multi-part answers
    rerank_top_k = 5 if question_data.get("test_capability") in ["aggregation and ranking", "cross-reference", "negative assertion"] else 3

    payload = {
        "query": question_data["question"],
        "collection_name": COLLECTION_NAME,
        "tenant_id": TENANT_ID,
        "search_top_k": 10,  # Speed-optimized (was 20)
        "rerank_top_k": rerank_top_k,  # Dynamic: 5 for complex queries, 3 for simple
        "enable_reranking": True,
        "enable_compression": False,  # Speed-optimized (was True)
        "compression_ratio": 0.5,
        "score_threshold": 0.3,
        "max_context_chunks": rerank_top_k,  # Match rerank_top_k to avoid additional filtering
        "enable_citations": False,  # Speed-optimized (was True)
        "use_metadata_boost": True,
        "temperature": 0.3,
        "stream": False  # Disable streaming for testing (need full JSON response with metadata)
        # "model" field intentionally omitted - use Intent Service recommendation or default
    }

    # Add response_style if provided (override auto-detection)
    if response_style:
        payload["response_style"] = response_style

    # Measure total time
    start_time = time.perf_counter()

    try:
        print(f"{Colors.BOLD}Sending query to retrieval API...{Colors.ENDC}")
        response = requests.post(
            RETRIEVAL_API_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=120  # 2 minutes timeout
        )

        end_time = time.perf_counter()
        total_time_ms = (end_time - start_time) * 1000

        response.raise_for_status()
        result = response.json()

        # Extract key metrics
        answer = result.get("answer", "")
        citations = result.get("citations", [])
        stages = result.get("stages", {})

        # Display results
        print(f"\n{Colors.OKGREEN}✅ SUCCESS!{Colors.ENDC}\n")

        print(f"{Colors.BOLD}Answer:{Colors.ENDC}")
        print(f"{answer}\n")

        print(f"{Colors.BOLD}Performance Metrics:{Colors.ENDC}")
        print(f"{Colors.OKBLUE}Total Time:{Colors.ENDC} {total_time_ms:,.2f} ms ({total_time_ms/1000:.2f}s)")
        print(f"{Colors.OKBLUE}Server Time:{Colors.ENDC} {result.get('total_time_ms', 0):,.2f} ms")
        print(f"{Colors.OKBLUE}Citations:{Colors.ENDC} {len(citations)}")
        print(f"{Colors.OKBLUE}Context Chunks:{Colors.ENDC} {result.get('context_count', 0)}")

        if stages:
            print(f"\n{Colors.BOLD}Pipeline Stages:{Colors.ENDC}")
            for stage_name, stage_data in stages.items():
                if isinstance(stage_data, dict):
                    stage_time = stage_data.get('time_ms', 0)
                    print(f"  {Colors.OKBLUE}{stage_name}:{Colors.ENDC} {stage_time:.2f} ms")

        # Calculate stage times first (needed for detailed analysis)
        server_time = result.get("total_time_ms", 1)
        stage_times = {
            "intent_detection": stages.get("intent_detection", {}).get("time_ms", 0) if isinstance(stages.get("intent_detection"), dict) else 0,
            "search": stages.get("search", {}).get("time_ms", 0) if isinstance(stages.get("search"), dict) else 0,
            "reranking": stages.get("reranking", {}).get("time_ms", 0) if isinstance(stages.get("reranking"), dict) else 0,
            "compression": stages.get("compression", {}).get("time_ms", 0) if isinstance(stages.get("compression"), dict) else 0,
            "answer_generation": stages.get("answer_generation", {}).get("time_ms", 0) if isinstance(stages.get("answer_generation"), dict) else 0
        }

        # IMPORTANT: Intent Detection and Search run in PARALLEL!
        # The bottleneck calculation shows which stage took longest, but Intent and Search
        # run simultaneously, so their times OVERLAP and should NOT be summed.
        #
        # Pipeline execution flow:
        #   t=0     -> Intent Detection + Search both start (PARALLEL)
        #   t=1.5s  -> Search completes (Embedding:512ms + Milvus:986ms + Boost:1.6ms)
        #   t=4.4s  -> Intent completes (actual intent=0.088ms, waits for parallel ops)
        #   t=4.4s  -> Reranking starts (sequential, needs Search results)
        #   t=4.8s  -> Answer Generation starts (sequential, needs Intent + Reranking)
        #
        # Total time = max(Intent, Search) + Reranking + Compression + Answer Generation
        # NOT = Intent + Search + Reranking + Compression + Answer (would double-count parallel time)
        #
        # If Intent shows high time (e.g., 4405ms), it's likely NOT Intent Service itself
        # being slow - Intent Service is instant (0.088ms pattern matching). The high time
        # is the total wait time for ALL parallel operations to complete.
        bottleneck_stage = max(stage_times, key=stage_times.get) if stage_times else "unknown"
        bottleneck_time = stage_times.get(bottleneck_stage, 0)
        bottleneck_percentage = (bottleneck_time / server_time * 100) if server_time > 0 else 0

        # Check for expected keywords
        answer_lower = answer.lower()
        keywords_found = [kw for kw in question_data['expected_answer_keywords'] if kw.lower() in answer_lower]
        keywords_missing = [kw for kw in question_data['expected_answer_keywords'] if kw.lower() not in answer_lower]

        print(f"\n{Colors.BOLD}Expected Keywords Analysis:{Colors.ENDC}")
        print(f"{Colors.OKGREEN}Found ({len(keywords_found)}):{Colors.ENDC} {', '.join(keywords_found) if keywords_found else 'None'}")
        if keywords_missing:
            print(f"{Colors.WARNING}Missing ({len(keywords_missing)}):{Colors.ENDC} {', '.join(keywords_missing)}")

        # Print detailed stage breakdown
        print(f"\n{Colors.BOLD}{'='*80}{Colors.ENDC}")
        print(f"{Colors.BOLD}DETAILED PIPELINE ANALYSIS{Colors.ENDC}")
        print(f"{Colors.BOLD}{'='*80}{Colors.ENDC}")

        # Intent Detection
        intent_metadata = stages.get("intent_detection", {}).get("metadata", {}) if isinstance(stages.get("intent_detection"), dict) else {}
        print(f"\n{Colors.OKCYAN}1. INTENT DETECTION ({stage_times.get('intent_detection', 0):.0f}ms - {(stage_times.get('intent_detection', 0)/server_time*100) if server_time > 0 else 0:.1f}% of total){Colors.ENDC}")
        print(f"   Intent: {intent_metadata.get('intent', 'unknown')}")
        print(f"   Language: {intent_metadata.get('language', 'unknown')}")
        print(f"   Complexity: {intent_metadata.get('complexity', 'unknown')}")
        print(f"   Confidence: {intent_metadata.get('confidence', 0)*100:.1f}%")
        print(f"   Recommended Model: {intent_metadata.get('recommended_model', 'unknown')}")
        print(f"   Custom Prompt: {'✅ Yes' if intent_metadata.get('has_custom_prompt') else '❌ No'}")

        # v2.0 Pattern Matcher Details
        analysis_method = intent_metadata.get('analysis_method', 'unknown')
        used_pattern = intent_metadata.get('used_pattern', False)
        print(f"   Detection Method: {'⚡ Pattern Match (v2.0)' if used_pattern else '🔍 LLM Fallback'}")

        # Show v2.0 pattern scoring details if available
        if 'pattern_scoring' in intent_metadata:
            pattern_scoring = intent_metadata['pattern_scoring']
            print(f"\n   {Colors.BOLD}📊 v2.0 Pattern Scoring:{Colors.ENDC}")
            print(f"      Scoring Version: {pattern_scoring.get('version', 'unknown')}")
            print(f"      Runner-up Intent: {pattern_scoring.get('runner_up', 'None')}")
            if pattern_scoring.get('runner_up'):
                print(f"      Runner-up Score: {pattern_scoring.get('runner_up_score', 0)*100:.1f}%")
                print(f"      Confidence Gap: {pattern_scoring.get('confidence_gap', 0)*100:.1f}%")

            # Multi-intent detection
            if pattern_scoring.get('multi_intent'):
                candidates = pattern_scoring.get('multi_intent_candidates', [])
                print(f"      ⚠️  Multi-Intent Query: {', '.join(candidates)}")

            # Show top 3 intent scores
            all_scores = pattern_scoring.get('all_scores', {})
            if all_scores:
                print(f"\n      {Colors.BOLD}Top Intent Scores:{Colors.ENDC}")
                sorted_scores = sorted(all_scores.items(), key=lambda x: x[1].get('final_score', 0), reverse=True)[:3]
                for idx, (intent_name, score_data) in enumerate(sorted_scores, 1):
                    final_score = score_data.get('final_score', 0) * 100
                    base_score = score_data.get('base_score', 0) * 100
                    patterns_matched = score_data.get('patterns_matched', 0)

                    marker = "🏆" if idx == 1 else f"  {idx}."
                    print(f"      {marker} {intent_name}: {final_score:.1f}% (base: {base_score:.1f}%, {patterns_matched} pattern(s))")

                    # Show penalties
                    penalties = score_data.get('penalties', [])
                    for reason, factor in penalties:
                        print(f"         - Penalty: {reason} (×{factor})")

                    # Show boosts
                    boosts = score_data.get('boosts', [])
                    for reason, factor in boosts:
                        print(f"         + Boost: {reason} (×{factor})")

        # Search
        search_metadata = stages.get("search", {}).get("metadata", {}) if isinstance(stages.get("search"), dict) else {}
        print(f"\n{Colors.OKCYAN}2. SEARCH ({stage_times.get('search', 0):.0f}ms - {(stage_times.get('search', 0)/server_time*100) if server_time > 0 else 0:.1f}% of total){Colors.ENDC}")
        print(f"   Results Retrieved: {result.get('search_results_count', 0)}")
        print(f"   Top K: {search_metadata.get('top_k', 20)}")
        print(f"   Metadata Boost: {'✅ Enabled' if search_metadata.get('metadata_boost_enabled') else '❌ Disabled'}")

        # Reranking
        rerank_metadata = stages.get("reranking", {}).get("metadata", {}) if isinstance(stages.get("reranking"), dict) else {}
        print(f"\n{Colors.OKCYAN}3. RERANKING ({stage_times.get('reranking', 0):.0f}ms - {(stage_times.get('reranking', 0)/server_time*100) if server_time > 0 else 0:.1f}% of total){Colors.ENDC}")
        print(f"   Input Chunks: {rerank_metadata.get('input_count', 0)}")
        print(f"   Output Chunks: {rerank_metadata.get('output_count', 0)}")
        print(f"   Reduction: {rerank_metadata.get('input_count', 0) - rerank_metadata.get('output_count', 0)} chunks filtered")

        # Compression
        compress_metadata = stages.get("compression", {}).get("metadata", {}) if isinstance(stages.get("compression"), dict) else {}
        compress_skipped = compress_metadata.get('skipped', False)
        print(f"\n{Colors.OKCYAN}4. COMPRESSION ({stage_times.get('compression', 0):.0f}ms){Colors.ENDC}")
        if compress_skipped:
            print(f"   Status: ⏭️  Skipped (not needed)")
        else:
            print(f"   Input: {result.get('reranked_count', 0)} chunks")
            print(f"   Output: {result.get('compressed_count', 0)} chunks")

        # Answer Generation
        answer_metadata = stages.get("answer_generation", {}).get("metadata", {}) if isinstance(stages.get("answer_generation"), dict) else {}
        print(f"\n{Colors.OKCYAN}5. ANSWER GENERATION ({stage_times.get('answer_generation', 0):.0f}ms - {(stage_times.get('answer_generation', 0)/server_time*100) if server_time > 0 else 0:.1f}% of total) {'🔴 BOTTLENECK' if bottleneck_stage == 'answer_generation' else ''}{Colors.ENDC}")
        print(f"   Model Requested: {answer_metadata.get('model_requested', 'unknown')}")
        print(f"   Model Used: {answer_metadata.get('model_used', 'unknown')}")
        print(f"   Used Recommended: {'✅ Yes' if answer_metadata.get('used_recommended_model') else '❌ No'}")
        print(f"   Custom Prompt: {'✅ Yes' if answer_metadata.get('used_custom_prompt') else '❌ No'}")
        print(f"   Temperature: {answer_metadata.get('temperature', 0)}")
        print(f"   Context Chunks: {result.get('context_count', 0)}")
        print(f"   Citations: {len(citations)}")

        # Bottleneck summary
        print(f"\n{Colors.WARNING}⚠️  BOTTLENECK: {bottleneck_stage.replace('_', ' ').title()} ({bottleneck_time:.0f}ms = {bottleneck_percentage:.1f}% of total time){Colors.ENDC}")

        print(f"{Colors.BOLD}{'='*80}{Colors.ENDC}")

        # Extract model and intent information (already calculated above)
        answer_gen_metadata = stages.get("answer_generation", {}).get("metadata", {}) if isinstance(stages.get("answer_generation"), dict) else {}
        intent_meta = stages.get("intent_detection", {}).get("metadata", {}) if isinstance(stages.get("intent_detection"), dict) else {}

        # Build result object
        test_result = {
            "test_id": question_data["id"],
            "category": question_data["category"],
            "question": question_data["question"],
            "difficulty": question_data["difficulty"],
            "test_capability": question_data["test_capability"],
            "timestamp": datetime.now().isoformat(),
            "success": True,
            "answer": answer,
            "citations_count": len(citations),
            "citations": citations,
            "performance": {
                "total_time_ms": total_time_ms,
                "server_time_ms": server_time,
                "network_latency_ms": total_time_ms - server_time,
                "stage_times": {
                    "intent_detection_ms": stage_times["intent_detection"],
                    "search_ms": stage_times["search"],
                    "reranking_ms": stage_times["reranking"],
                    "compression_ms": stage_times["compression"],
                    "answer_generation_ms": stage_times["answer_generation"]
                },
                "stage_percentages": {
                    "intent_detection_pct": (stage_times["intent_detection"] / server_time * 100) if server_time > 0 else 0,
                    "search_pct": (stage_times["search"] / server_time * 100) if server_time > 0 else 0,
                    "reranking_pct": (stage_times["reranking"] / server_time * 100) if server_time > 0 else 0,
                    "compression_pct": (stage_times["compression"] / server_time * 100) if server_time > 0 else 0,
                    "answer_generation_pct": (stage_times["answer_generation"] / server_time * 100) if server_time > 0 else 0
                },
                "bottleneck": {
                    "stage": bottleneck_stage,
                    "time_ms": bottleneck_time,
                    "percentage_of_total": bottleneck_percentage
                }
            },
            "retrieval_metrics": {
                "search_results_count": result.get("search_results_count", 0),
                "reranked_count": result.get("reranked_count", 0),
                "compressed_count": result.get("compressed_count", 0),
                "context_count": result.get("context_count", 0)
            },
            "models_used": {
                "llm_requested": answer_gen_metadata.get("model_requested"),
                "llm_used": answer_gen_metadata.get("model_used"),
                "llm_temperature": answer_gen_metadata.get("temperature"),
                "used_recommended_model": answer_gen_metadata.get("used_recommended_model"),
                "used_custom_prompt": answer_gen_metadata.get("used_custom_prompt")
            },
            "intent_analysis": {
                "detected_intent": intent_meta.get("intent"),
                "language": intent_meta.get("language"),
                "complexity": intent_meta.get("complexity"),
                "confidence": intent_meta.get("confidence"),
                "recommended_model": intent_meta.get("recommended_model"),
                "has_custom_prompt": intent_meta.get("has_custom_prompt")
            },
            "keyword_analysis": {
                "expected_keywords": question_data["expected_answer_keywords"],
                "keywords_found": keywords_found,
                "keywords_missing": keywords_missing,
                "coverage_percentage": (len(keywords_found) / len(question_data["expected_answer_keywords"]) * 100) if question_data["expected_answer_keywords"] else 0
            },
            "full_response": result
        }

        return test_result

    except requests.exceptions.HTTPError as e:
        end_time = time.perf_counter()
        total_time_ms = (end_time - start_time) * 1000

        print(f"{Colors.FAIL}❌ HTTP Error: {e}{Colors.ENDC}")
        print(f"{Colors.FAIL}Response: {e.response.text if hasattr(e, 'response') else 'N/A'}{Colors.ENDC}")

        return {
            "test_id": question_data["id"],
            "category": question_data["category"],
            "question": question_data["question"],
            "difficulty": question_data["difficulty"],
            "test_capability": question_data["test_capability"],
            "timestamp": datetime.now().isoformat(),
            "success": False,
            "error": str(e),
            "error_response": e.response.text if hasattr(e, 'response') else None,
            "performance": {
                "total_time_ms": total_time_ms
            }
        }

    except Exception as e:
        end_time = time.perf_counter()
        total_time_ms = (end_time - start_time) * 1000

        print(f"{Colors.FAIL}❌ Error: {e}{Colors.ENDC}")

        return {
            "test_id": question_data["id"],
            "category": question_data["category"],
            "question": question_data["question"],
            "difficulty": question_data["difficulty"],
            "test_capability": question_data["test_capability"],
            "timestamp": datetime.now().isoformat(),
            "success": False,
            "error": str(e),
            "performance": {
                "total_time_ms": total_time_ms
            }
        }

def main():
    """Main test runner"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Q&A Retrieval Testing Suite',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_qa_tests.py                          # Run all tests with default settings
  python run_qa_tests.py --test-ids 7.5           # Run only Query 7.5
  python run_qa_tests.py --test-ids 7.1 7.2       # Run Query 7.1 and 7.2
  python run_qa_tests.py --response-style concise # Run all tests with concise answers
  python run_qa_tests.py --test-ids 7.5 --response-style balanced  # Query 7.5 with balanced style
        """
    )

    parser.add_argument(
        '--test-ids',
        nargs='+',
        help='Specific test IDs to run (e.g., 1.1 1.2 7.5)',
        metavar='ID'
    )

    parser.add_argument(
        '--response-style',
        choices=['concise', 'balanced', 'comprehensive'],
        help='Override answer verbosity style: concise (2-4 bullets), balanced (moderate detail), comprehensive (full analysis)',
        metavar='STYLE'
    )

    args = parser.parse_args()

    # Filter questions if specific IDs provided
    if args.test_ids:
        questions_to_run = [q for q in TEST_QUESTIONS if q['id'] in args.test_ids]
        if not questions_to_run:
            print(f"{Colors.FAIL}❌ No matching test IDs found: {args.test_ids}{Colors.ENDC}")
            print(f"{Colors.WARNING}Available IDs: {', '.join([q['id'] for q in TEST_QUESTIONS])}{Colors.ENDC}")
            return
    else:
        questions_to_run = TEST_QUESTIONS

    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*100}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'Q&A Retrieval Testing Suite'.center(100)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*100}{Colors.ENDC}\n")

    print(f"{Colors.BOLD}Configuration:{Colors.ENDC}")
    print(f"{Colors.OKCYAN}Retrieval API:{Colors.ENDC} {RETRIEVAL_API_URL}")
    print(f"{Colors.OKCYAN}Collection:{Colors.ENDC} {COLLECTION_NAME}")
    if args.test_ids:
        print(f"{Colors.OKCYAN}Running Specific Tests:{Colors.ENDC} --test-ids, {', '.join(args.test_ids)}")
    if args.response_style:
        print(f"{Colors.OKCYAN}Response Style:{Colors.ENDC} {args.response_style.upper()} (override)")
    print(f"{Colors.OKCYAN}Total Questions:{Colors.ENDC} {len(questions_to_run)}")
    print(f"{Colors.OKCYAN}Results Directory:{Colors.ENDC} {RESULTS_DIR}\n")

    # Check API health
    print(f"{Colors.BOLD}Checking retrieval API health...{Colors.ENDC}")
    is_healthy, health_data = check_api_health()

    if not is_healthy:
        print(f"{Colors.FAIL}❌ Retrieval API is not running or unhealthy!{Colors.ENDC}")
        print(f"{Colors.FAIL}Error: {health_data}{Colors.ENDC}")
        print(f"\n{Colors.WARNING}Please start the retrieval pipeline services first.{Colors.ENDC}")
        print(f"{Colors.WARNING}Run: cd /Users/rakesh/Desktop/crawlenginepro.mindmate247.com/code/Tools && ./pipeline-manager start-retrieval{Colors.ENDC}\n")
        return

    print(f"{Colors.OKGREEN}✅ Retrieval API is healthy{Colors.ENDC}")
    if health_data:
        print(f"{Colors.OKBLUE}Status:{Colors.ENDC} {health_data.get('status')}")
        print(f"{Colors.OKBLUE}Version:{Colors.ENDC} {health_data.get('version')}")
        deps = health_data.get('dependencies', {})
        healthy_deps = sum(1 for d in deps.values() if d.get('status') == 'healthy')
        print(f"{Colors.OKBLUE}Dependencies:{Colors.ENDC} {healthy_deps}/{len(deps)} healthy\n")

    # Get service models and cache status
    print(f"{Colors.BOLD}Collecting service information...{Colors.ENDC}")
    services_info = get_service_models_and_cache()

    # Display service information
    print(f"{Colors.BOLD}Service Configuration:{Colors.ENDC}")
    if "embeddings" in services_info and "error" not in services_info["embeddings"]:
        emb = services_info["embeddings"]
        print(f"{Colors.OKCYAN}Embedding Model:{Colors.ENDC} {emb.get('model')} ({emb.get('dimension')}-dim)")
        print(f"{Colors.OKCYAN}Embedding Provider:{Colors.ENDC} {emb.get('provider')} on {emb.get('device')}")
        cache_status = "🔴 ENABLED" if emb.get('cache_enabled') else "✅ DISABLED"
        print(f"{Colors.OKCYAN}Embeddings Cache:{Colors.ENDC} {cache_status}")

    if "reranking" in services_info and "error" not in services_info["reranking"]:
        rerank = services_info["reranking"]
        print(f"{Colors.OKCYAN}Reranking Model:{Colors.ENDC} {rerank.get('model')}")

    if "answer_generation" in services_info and "error" not in services_info["answer_generation"]:
        ans_cache = services_info["answer_generation"].get("cache_enabled", False)
        cache_status = "🔴 ENABLED" if ans_cache else "✅ DISABLED"
        print(f"{Colors.OKCYAN}Answer Cache:{Colors.ENDC} {cache_status}")

    print()

    # Run all tests
    all_results = []
    test_start_time = time.time()

    for idx, question in enumerate(questions_to_run, 1):
        result = run_single_query(question, idx, len(questions_to_run), args.response_style)
        all_results.append(result)

        # Small delay between tests to avoid overwhelming the API
        if idx < len(questions_to_run):
            time.sleep(0.5)

    test_end_time = time.time()
    total_test_time = test_end_time - test_start_time

    # Calculate summary statistics
    successful_tests = [r for r in all_results if r.get("success")]
    failed_tests = [r for r in all_results if not r.get("success")]

    avg_total_time = sum(r.get("performance", {}).get("total_time_ms", 0) for r in successful_tests) / len(successful_tests) if successful_tests else 0
    avg_server_time = sum(r.get("performance", {}).get("server_time_ms", 0) for r in successful_tests) / len(successful_tests) if successful_tests else 0

    avg_keyword_coverage = sum(r.get("keyword_analysis", {}).get("coverage_percentage", 0) for r in successful_tests) / len(successful_tests) if successful_tests else 0

    # Category-wise performance
    category_stats = {}
    for result in successful_tests:
        category = result.get("category")
        if category not in category_stats:
            category_stats[category] = {
                "count": 0,
                "total_time": 0,
                "keyword_coverage": []
            }
        category_stats[category]["count"] += 1
        category_stats[category]["total_time"] += result.get("performance", {}).get("total_time_ms", 0)
        category_stats[category]["keyword_coverage"].append(result.get("keyword_analysis", {}).get("coverage_percentage", 0))

    # Build summary object
    summary = {
        "test_run_timestamp": datetime.now().isoformat(),
        "collection_name": COLLECTION_NAME,
        "total_questions": len(TEST_QUESTIONS),
        "successful_tests": len(successful_tests),
        "failed_tests": len(failed_tests),
        "total_test_duration_seconds": total_test_time,
        "service_configuration": services_info,
        "average_metrics": {
            "total_time_ms": avg_total_time,
            "server_time_ms": avg_server_time,
            "keyword_coverage_percentage": avg_keyword_coverage
        },
        "category_statistics": {
            cat: {
                "test_count": stats["count"],
                "avg_time_ms": stats["total_time"] / stats["count"],
                "avg_keyword_coverage": sum(stats["keyword_coverage"]) / len(stats["keyword_coverage"]) if stats["keyword_coverage"] else 0
            }
            for cat, stats in category_stats.items()
        }
    }

    # Save results to JSON
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = RESULTS_DIR / f"qa_test_results_{timestamp_str}.json"

    output_data = {
        "summary": summary,
        "test_results": all_results
    }

    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    # Display summary
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*100}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'Test Summary'.center(100)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*100}{Colors.ENDC}\n")

    print(f"{Colors.BOLD}Overall Results:{Colors.ENDC}")
    print(f"{Colors.OKGREEN}✅ Successful:{Colors.ENDC} {len(successful_tests)}/{len(TEST_QUESTIONS)}")
    if failed_tests:
        print(f"{Colors.FAIL}❌ Failed:{Colors.ENDC} {len(failed_tests)}/{len(TEST_QUESTIONS)}")

    print(f"\n{Colors.BOLD}Performance Averages:{Colors.ENDC}")
    print(f"{Colors.OKBLUE}Avg Total Time:{Colors.ENDC} {avg_total_time:,.2f} ms ({avg_total_time/1000:.2f}s)")
    print(f"{Colors.OKBLUE}Avg Server Time:{Colors.ENDC} {avg_server_time:,.2f} ms ({avg_server_time/1000:.2f}s)")
    print(f"{Colors.OKBLUE}Avg Keyword Coverage:{Colors.ENDC} {avg_keyword_coverage:.1f}%")

    print(f"\n{Colors.BOLD}Category Performance:{Colors.ENDC}")
    for category, stats in summary["category_statistics"].items():
        print(f"{Colors.OKCYAN}{category}:{Colors.ENDC}")
        print(f"  Tests: {stats['test_count']}")
        print(f"  Avg Time: {stats['avg_time_ms']:,.2f} ms")
        print(f"  Avg Coverage: {stats['avg_keyword_coverage']:.1f}%")

    print(f"\n{Colors.BOLD}Results saved to:{Colors.ENDC}")
    print(f"{Colors.OKGREEN}{results_file}{Colors.ENDC}\n")

    print(f"{Colors.OKGREEN}✅ All tests completed!{Colors.ENDC}\n")

if __name__ == "__main__":
    main()
