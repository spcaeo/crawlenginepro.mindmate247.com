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
python run_qa_tests.py 1.1

# Multiple tests
python run_qa_tests.py 1.1 1.2 2.1
```

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
   - **Answer Generation**: Models used (requested vs actual), context chunks
   - **Bottleneck Identification**: Slowest stage highlighted

4. **Test Summary**
   - Success rate
   - Performance averages
   - Category breakdown

### JSON Output
Results saved to: `../results/qa_test_results_YYYYMMDD_HHMMSS.json`

Contains complete details:
- Query text and metadata
- Full answer
- Performance metrics
- Pipeline stage breakdown
- Context chunks and citations
- Expected keywords analysis

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
Timeline:
t=0ms    ├─ Intent Detection starts ────────────────┐ (completes at 4.4s)
         ├─ Search starts ──────────────┐            │
         │                               │            │
         │   Embedding: 512ms            │            │
         │   Milvus: 986ms               │            │
         │   Metadata Boost: 1.6ms       │            │
         │                               │            │
t=1.5s   └─ Search completes ────────────┘            │
t=4.4s   └─ Intent completes ────────────────────────┘
         ├─ Reranking starts (uses Search results)
         ├─ Answer Generation starts (uses Intent + Search)
```

**What This Means:**
- Intent shows "4405ms" but it doesn't ADD 4.4 seconds to total time
- Search shows "1500ms" and completes first
- Total pipeline time = max(Intent, Search) + Reranking + Answer
- **Don't sum all stage times** - Intent and Search overlap!

**Actual Bottlenecks:**
1. **Intent Detection (4.4s)** - Runs in parallel, but holds up Answer Generation
2. **Milvus Search (1.0s)** - 66% of Search time, runs in parallel with Intent
3. **Answer Generation** - Waits for both Intent and Search to complete

**Why Intent Can Show High Time:**
- Intent Service itself is INSTANT (0.088ms) using pattern matching
- The 4.4s is the total time it waits for parallel operations
- This is NOT a bottleneck in Intent Service itself

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
