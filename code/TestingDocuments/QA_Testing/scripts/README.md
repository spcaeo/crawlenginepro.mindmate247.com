# Q&A Testing Suite

## Overview
Automated testing suite for evaluating the RAG (Retrieval-Augmented Generation) pipeline's accuracy and performance across 18 carefully designed test questions.

## Prerequisites
- All pipeline services must be running:
  - **Ingestion Pipeline** (ports 8070-8079)
  - **Retrieval Pipeline** (ports 8090-8099)
- Cache must be **DISABLED** for accurate testing
- Collection `jina_v3_test` must be populated with test data

## Usage

### Run All Tests (18 questions)
```bash
python run_qa_tests.py
```

### Run Specific Tests
```bash
# Single test
python run_qa_tests.py --test-ids 1.1

# Multiple tests
python run_qa_tests.py --test-ids 1.1 1.2 2.1
```

### Run with Diagnostic Mode (7-Field Metadata Validation)
```bash
# Enable diagnostic mode to validate all 7 metadata fields
python run_qa_tests.py --diagnostic

# Combine with specific test
python run_qa_tests.py --test-ids 3.1 --diagnostic

# Full diagnostic run with response style override
python run_qa_tests.py --test-ids 7.7 --diagnostic --response-style balanced
```

**Diagnostic Mode Features:**
1. **Metadata Boost Breakdown** - Shows contribution from all 7 fields per search result:
   - Standard fields (4): keywords, topics, questions, summary
   - Enhanced fields (3): semantic_keywords, entity_relationships, attributes
2. **Chunk Metadata Inspection** - Direct Milvus query to verify field presence and quality
3. **Per-Field Statistics** - Coverage percentage, average length, sample values

### Run with Response Style Override
```bash
# Override answer style (default: auto-detected by Intent Service)
python run_qa_tests.py --test-ids 7.2 --response-style concise
python run_qa_tests.py --test-ids 7.2 --response-style balanced
python run_qa_tests.py --test-ids 7.2 --response-style comprehensive

# Combine with diagnostic mode
python run_qa_tests.py --test-ids 7.2 --response-style comprehensive --diagnostic
```

**Response Style Options:**
- **concise**: Brief, direct answers with minimal explanation
- **balanced**: Moderate detail with key explanations (default recommendation)
- **comprehensive**: Detailed answers with full context and step-by-step reasoning
- **auto-detected** (default): Intent Service chooses based on query complexity

**Response Style Performance (Query 7.2 example):**
| Style | Total Time | Answer Gen | Answer Length |
|-------|------------|------------|---------------|
| concise | 4.2s | 2.0s | ~250 words |
| balanced | 5.1s | 2.8s | ~200 words |
| comprehensive | 3.8s ✅ | 1.9s ✅ | ~210 words |

*Note: Performance varies by query complexity and LLM API latency. Testing shows "comprehensive" paradoxically performs best for arithmetic queries.*

### Available Test IDs
- **1.1 - 1.6**: Cross-Section Synthesis (hard)
- **2.1 - 2.6**: Multi-Hop Reasoning (medium)
- **3.1 - 3.6**: Single-Document Focused (easy)

## Output

### Console Output
The script provides detailed analysis including:

1. **Service Configuration**
   - Embedding model and provider
   - Cache status (must be DISABLED)
   - Reranking model

2. **For Each Query**
   - Full answer text
   - Performance metrics (total time, citations, chunks)
   - Expected keyword coverage

3. **Detailed Pipeline Analysis**
   - **Intent Detection**: Intent type, confidence, recommended model, detection method (pattern vs LLM)
   - **v2.0 Pattern Matcher Scoring** (when pattern used):
     - Scoring version (2.0)
     - Runner-up intent and confidence gap
     - Top 3 intent scores with base scores
     - Penalties applied (conflict resolution)
     - Boosts applied (multi-pattern, position, length)
     - Multi-intent detection flags
   - **Search**: Results retrieved, metadata boost status
   - **Reranking**: Input/output chunk counts
   - **Compression**: Status
   - **Answer Generation**: Models used (requested vs actual), response style, context chunks
   - **Response Style**: Shows if auto-detected or manually overridden (concise/balanced/comprehensive)
   - **Bottleneck Identification**: Slowest stage highlighted with projected optimization savings

4. **Test Summary**
   - Success rate
   - Performance averages
   - Category breakdown

### JSON Output
Results saved to: `../results/qa_test_results_YYYYMMDD_HHMMSS.json`

Contains complete details:
- Query text and metadata
- Full answer
- Performance metrics (with parallel execution breakdown)
- Pipeline stage breakdown
- Context chunks and citations
- Expected keywords analysis
- Response style information:
  - `response_style`: "concise", "balanced", "comprehensive", or "auto-detected"
  - `response_style_override`: true if manually set via --response-style flag
- Parallel execution metrics:
  - Intent and Search times (run in parallel)
  - Parallel time (max of both, NOT sum)
  - Time saved by parallel execution
  - Blocking stage and blocking time beyond other parallel stage

## Key Metrics Tracked

### Performance
- Total time (client + network)
- Server time (backend processing)
- Stage-by-stage breakdown:
  - Intent detection time
  - Search time
  - Reranking time
  - Compression time (if used)
  - Answer generation time
- Bottleneck identification

**IMPORTANT: Understanding Parallel Execution Timing**

The Retrieval Pipeline runs **Intent Detection** and **Search** stages in **PARALLEL** to improve performance:

```
Timeline Example (Query 7.1):
t=0ms    ├─ Intent Detection starts ────────────────┐ (completes at 2.9s)
         ├─ Search starts ──────────────┐            │
         │                               │            │
         │   Embedding: ~500ms           │            │
         │   Milvus: ~900ms              │            │
         │   Metadata Boost: ~2ms        │            │
         │                               │            │
t=1.4s   └─ Search completes ────────────┘            │
t=2.9s   └─ Intent completes ────────────────────────┘
         ├─ Reranking starts (uses Search results) ──┐
t=3.4s   ├─ Reranking completes (527ms) ──────────────┘
         ├─ Answer Generation starts (uses Intent + Reranking results) ──┐
t=5.3s   └─ Answer completes (1898ms) ───────────────────────────────────┘

Total Time: 3.9s
```

**Critical Understanding:**
- Intent shows "2934ms" and Search shows "1429ms"
- **These times OVERLAP** - they run simultaneously
- Parallel phase time = max(2934, 1429) = 2934ms (NOT 2934 + 1429 = 4363ms!)
- Sequential phase time = Reranking (527ms) + Answer (1898ms) = 2425ms
- Total ≈ 2934 + 2425 = 5359ms (but with some overlap, actual = 3860ms)

**How to Read Stage Times:**
1. **Intent Detection: 2934ms (76% of total)** [PARALLEL with Search]
   - This is the ACTUAL time Intent takes (including LLM call)
   - But only adds 2934 - 1429 = 1505ms to total (time beyond Search)
2. **Search: 1429ms (37% of total)** [PARALLEL with Intent]
   - This is the ACTUAL time Search takes
   - Completes before Intent finishes
3. **Reranking: 527ms (14% of total)** [SEQUENTIAL - waits for Search]
4. **Answer: 1898ms (49% of total)** [SEQUENTIAL - waits for Intent + Reranking]

**Bottleneck Analysis:**
- If Intent = 2934ms and Search = 1429ms → **Intent is blocking by 1505ms**
- Optimizing Intent to <100ms would save 1505ms from total time
- Total would drop from 3860ms → ~2355ms (achieving 2-3s goal!)

**Common Mistake:**
❌ "Total time should be 2934 + 1429 + 527 + 1898 = 6788ms, why is it only 3860ms?"
✅ Correct: "Total = max(2934, 1429) + 527 + 1898 ≈ 3860ms (with some overlap)"

**Percentages Explained:**
- Stage percentages add up to MORE than 100% because Intent and Search overlap
- Intent: 76% + Search: 37% + Reranking: 14% + Answer: 49% = 176% total
- This is EXPECTED - the 76% overlap is the time saved by parallel execution

### Quality
- Expected keyword coverage
- Citation count
- Context chunks used

### Configuration
- Models used at each stage
- Cache status verification
- Model routing decisions (requested vs used)

## Important Notes

1. **Cache Must Be Disabled**
   - Embeddings cache: `cache_enabled: false`
   - Answer cache: `cache: false`
   - Script verifies this before running

2. **Model Selection**
   - Intent detection recommends appropriate model size
   - Answer service may use different model than configured
   - This is "intelligent routing" to optimize cost/performance

3. **Results Review**
   - Review detailed console output for each query
   - JSON files are for archival reference only
   - Focus on bottleneck identification for optimization

## Diagnostic Mode Output

### Example: 7-Field Metadata Validation
```
================================================================================
DIAGNOSTIC MODE: 7-FIELD METADATA VALIDATION
================================================================================

1. METADATA BOOST BREAKDOWN (All 7 Fields)
✅ Successfully retrieved metadata boost details
Metadata Boost Applied: Yes
Results Analyzed: 3

  Result #1: ComprehensiveTestDocument_chunk_0002...
    Vector Score: 0.8234
    Metadata Boost: +0.0850
    Final Score: 0.9084

    Standard Metadata (4 fields):
      Keywords Matched: 3 - ['Nike', 'Pegasus', 'running']
      Topics Matched: 2 - ['running shoes', 'athletic footwear']
      Question Similarity: 0.65
      Summary Coverage: 0.80

    Enhanced Metadata (3 NEW fields):
      ✓ Semantic Keywords: 5 - ['athletic', 'performance', 'cushioning']
      ✓ Entity Relationships: 0.75
      ✓ Attributes Coverage: 0.60

2. CHUNK METADATA FIELD INSPECTION
✅ Successfully inspected 3 chunks

Standard Metadata Fields (4):
  ✓ keywords            : 3/3 (100.0%) | Avg:  207 chars
      Sample: Nike Air Zoom Pegasus 40, Nike Inc., Air Zoom Pegasus 40, NIKE-PEGASUS-40-MEN...
  ✓ topics              : 3/3 (100.0%) | Avg:   47 chars
      Sample: running shoes, athletic footwear, Nike products
  ✓ questions           : 3/3 (100.0%) | Avg:  194 chars
      Sample: What is the Nike Air Zoom Pegasus 40? | Why is the Nike Air Zoom Pegasus 40...
  ✓ summary             : 3/3 (100.0%) | Avg:  213 chars
      Sample: The Nike Air Zoom Pegasus 40 is a 2023 running shoe featuring React foam...

Enhanced Metadata Fields (3 NEW):
  ✓ semantic_keywords   : 3/3 (100.0%) | Avg:  186 chars
      Sample: athletic shoes, running sneakers, cushioned footwear, breathable uppers...
  ✓ entity_relationships: 3/3 (100.0%) | Avg:  275 chars
      Sample: Nike Inc. → manufacturer-of → Nike Air Zoom Pegasus 40 | Nike Inc. → brand...
  ✓ attributes          : 3/3 (100.0%) | Avg:  262 chars
      Sample: brand: Nike Inc., manufacturer: Nike Inc., model: Air Zoom Pegasus 40, SKU...
================================================================================
```

**What This Tells You:**
- ✅ All 7 metadata fields are present and populated
- ✅ Enhanced fields (semantic_keywords, entity_relationships, attributes) are contributing to search boost
- ✅ Field quality is good (reasonable average lengths, meaningful content)
- ⚠️ If any field shows 0% coverage or empty samples, metadata generation may need review

## Example Output

### Example 1: Pattern Match (v2.0) - Fast Path
```
Query 7.7 Results
Performance:
- Total Time: 1,123ms (1.1s)
- Intent Detection: 0.2ms (⚡ PATTERN MATCH)
- Search: 823ms (73.4%)
- Reranking: 245ms (21.8%)
- Answer Generation: 300ms (26.7%)

Intent Detection:
- Intent: relationship_mapping
- Confidence: 100%
- Detection Method: ⚡ Pattern Match (v2.0)
- Custom Prompt: ✅ Yes

📊 v2.0 Pattern Scoring:
   Scoring Version: 2.0
   Runner-up Intent: list_enumeration
   Runner-up Score: 67.9%
   Confidence Gap: 32.1%

   Top Intent Scores:
   🏆 relationship_mapping: 100.0% (base: 93.0%, 1 pattern(s))
      + Boost: Pattern at query start (×1.10)
      + Boost: Long pattern match (×1.15)
   2. list_enumeration: 67.9% (base: 95.0%, 1 pattern(s))
      - Penalty: Too generic - specific intent takes precedence (×0.65)
      + Boost: Pattern at query start (×1.10)

Answer Quality:
- Found 4/5 expected keywords (80%)
- 3 citations used
- 3 context chunks
```

### Example 2: LLM Fallback - When No Pattern Matches
```
Query 7.1 Results
Performance:
- Total Time: 7,233ms (7.2s)
- Intent Detection: 6,906ms (🔍 LLM FALLBACK)
- Search: 1,334ms (18.4%)
- Reranking: 598ms (8.3%)
- Answer Generation: 5,297ms (73.3%) 🔴 BOTTLENECK

Intent Detection:
- Intent: negative_logic
- Confidence: 95%
- Detection Method: 🔍 LLM Fallback (no pattern matched)
- Custom Prompt: ✅ Yes
- ⚠️ SLOW: No negative_logic patterns in library

Answer Quality:
- Found all 5 expected keywords (100%)
- 2 citations used
- 5 context chunks

Models Used:
- LLM Requested: Llama-3.3-70B-Instruct
- LLM Used: Meta-Llama-3.3-70B-Instruct (recommended by intent detection)
```

## Understanding v2.0 Pattern Matcher Output

The test suite now displays detailed v2.0 pattern matching scoring to help verify the regex system is working correctly.

### Detection Method

```
Detection Method: ⚡ Pattern Match (v2.0)  ← Fast path (<1ms)
Detection Method: 🔍 LLM Fallback         ← Slow path (~2-7s, no pattern matched)
```

**What to look for:**
- ⚡ Pattern Match = GOOD (sub-millisecond intent detection)
- 🔍 LLM Fallback = Consider adding pattern for this intent to speed up

### Pattern Scoring Breakdown

When a pattern matches, you'll see:

```
📊 v2.0 Pattern Scoring:
   Scoring Version: 2.0
   Runner-up Intent: list_enumeration      ← Second-best intent
   Runner-up Score: 67.9%                  ← How confident in runner-up
   Confidence Gap: 32.1%                   ← Winner's margin (higher = more confident)
```

**Confidence Gap Analysis:**
- **>30%:** Very confident, clear winner
- **20-30%:** Confident, good separation
- **10-20%:** Moderate confidence, review if accuracy issues
- **<10%:** Low confidence, may need pattern refinement

### Top Intent Scores

Shows top 3 competing intents with full scoring breakdown:

```
Top Intent Scores:
🏆 relationship_mapping: 100.0% (base: 93.0%, 1 pattern(s))
   + Boost: Pattern at query start (×1.10)       ← 10% boost
   + Boost: Long pattern match (×1.15)           ← 15% boost
2. list_enumeration: 67.9% (base: 95.0%, 1 pattern(s))
   - Penalty: Too generic (×0.65)                ← 35% penalty
   + Boost: Pattern at query start (×1.10)
```

**How Scoring Works:**
1. **Base Score:** Pattern's confidence (from pattern_library.json)
2. **Penalties:** Applied when generic intent conflicts with specific intent
3. **Boosts:** Rewards for strong match signals (early position, long match, multiple patterns)
4. **Final Score:** base × penalty × boosts (capped at 100%)

**Common Penalties:**
- `list_enumeration` penalized when `relationship_mapping` matches (×0.65)
- `factual_retrieval` penalized when `comparison` matches (×0.75)
- `definition_explanation` penalized when `simple_lookup` matches (×0.70)

**Common Boosts:**
- Multi-pattern boost: 2+ patterns match (×1.25)
- Early position boost: Pattern at query start (×1.10)
- Long match boost: Pattern matches 30+ chars (×1.15)

### Multi-Intent Detection

```
⚠️  Multi-Intent Query: relationship_mapping, cross_reference
```

Flags when multiple intents score >85% - may need query clarification or multi-part answer.

### What This Tells You

1. **Performance:** Pattern match vs LLM fallback time
2. **Accuracy:** Confidence gap between winner and runner-up
3. **Conflict Resolution:** See penalties/boosts in action
4. **Coverage Gaps:** LLM fallbacks indicate missing patterns

**Action Items Based on Output:**
- 🔍 LLM Fallback + high time → Add pattern for this intent
- Low confidence gap (<20%) → Review pattern specificity
- ⚠️ Multi-Intent → Check if query needs both intents or pattern is too broad

## Troubleshooting

### Services Not Running
```
❌ Retrieval API is not healthy
```
**Solution**: Start pipelines using `./pipeline-manager start-ingestion` and `./pipeline-manager start-retrieval`

### No Matching Test IDs
```
❌ No matching test IDs found: X.Y
```
**Solution**: Check available IDs with `python run_qa_tests.py` (will list all 18 tests)

### Cache Enabled Warning
If cache is detected as enabled, disable it in:
- `/code/shared/.env.dev`: Set `ENABLE_CACHE=false`
- Restart all services after changing
