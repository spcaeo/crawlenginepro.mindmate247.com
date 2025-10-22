# RAG & Vector Search Test Query Matrix

## Overview
This document contains a comprehensive test suite designed to challenge retrieval-augmented generation (RAG) and vector search services. The queries test various capabilities including cross-referencing, synthesis, contextual reasoning, mathematical operations, and multi-hop logic.

---

## Category 1: Cross-Section Synthesis Queries

### Query 1.1: Technology Comparison Across Sections
**Question:** "Compare the technical terms used in the Nike Air Zoom Pegasus 40 and Michelin Pilot Sport 4S Tire sections; what technologies do they share?"

**Answer:**
- Nike Air Zoom Pegasus 40 technical terms: React foam technology, Zoom Air cushioning, engineered mesh, waffle-pattern traction
- Michelin Pilot Sport 4S Tire technical terms: Bi-compound technology, Dynamic Response Technology, Variable Contact Patch 3.0, Hybrid Aramid/Nylon belt package
- Shared/Similar Technologies: Both emphasize advanced material science for performance—Nike uses engineered mesh for breathability and traction, while Michelin uses bi-compound tread and hybrid belt for grip and handling. No direct overlap in proprietary technologies, but both focus on comfort, traction, and responsiveness.

**Reason for Difficulty:** Requires synthesizing technical terminology across unrelated product categories and identifying thematic similarities rather than exact matches.

**Expected RAG/Vector Behavior:** Most systems will return isolated details about Nike or Michelin separately, listing technical terms from each section but not synthesizing similarities. They'll likely miss nuanced links like shared emphasis on 'traction' or 'performance' unless explicitly connected in text.

**Notes:** Tests semantic understanding and cross-domain synthesis capabilities.

---

### Query 1.2: Vendor Cross-Reference
**Question:** "Which vendors appear in both technology and medical equipment invoices, and what are their order statuses?"

**Answer:**
- Technology invoice vendor: TechSupply Solutions
- Medical equipment invoice vendor: MedTech Equipment Supply
- Order statuses: Technology (Paid); Medical Equipment (Net 30 - Due 2024-03-30)
- Overlap: There is no vendor appearing in both invoices, and each order has its own distinct status

**Reason for Difficulty:** Requires checking multiple invoice sections, comparing vendor lists, and accurately reporting absence of overlap.

**Expected RAG/Vector Behavior:** Most systems will list vendors and statuses for each invoice section but generally do not detect or report absence of overlap unless it's stated directly.

**Notes:** Tests ability to perform negative assertions and cross-document entity matching.

---

### Query 1.3: Highest-Priced Product with Full Specifications
**Question:** "Find the highest-priced 
roduct listed across all invoices and describe its key features and technical specifications."

**Answer:**
- The highest-priced product is the Hobart Commercial Dishwasher (Model LXeR-2) at $8,999.00 USD
- Key features and technical specifications: High-temperature sanitizing, 40 racks/hour capacity, Energy Star certified, chemical/solid waste pumping system, dimensions 24.5 x 25 x 34 inches

**Reason for Difficulty:** Requires aggregating prices across all invoices, ranking them, then retrieving associated specifications in a single integrated response.

**Expected RAG/Vector Behavior:** Typical systems may focus on price extraction but miss relating features/specs in a single, concise response. May not rank all products across invoices unless one query retrieves all prices and another the associated features.

**Notes:** Tests global document search with aggregation and ranking capabilities.

---

## Category 2: Negative/Not-Found Testing

### Query 2.1: Non-Existent Information
**Question:** "What is the refund policy for any of the vendors listed?"

**Answer:** Not found - There is no information on refund policy for any product or vendor in the provided document.

**Reason for Difficulty:** Tests whether the system can confidently state information doesn't exist rather than hallucinating or fabricating an answer.

**Expected RAG/Vector Behavior:** Correctly implemented systems should respond with "not found" or similar indication. Poor systems may fabricate policies or provide tangential information.

**Notes:** Critical test for hallucination detection and factual accuracy.

---

## Category 3: Standard Ecommerce Queries

### Query 3.1: Basic Product Information Retrieval
**Question:** "What is the price and key specifications of the Apple iPhone 15 Pro Max listed in the catalog?"

**Answer:**
- Price: $1,199 USD
- Major features: A17 Pro chip, 256GB storage, triple camera system with 48MP main, 12MP ultra wide, 12MP telephoto, 5x optical zoom, ProMotion 120Hz display, titanium design

**Reason for Difficulty:** Straightforward retrieval from a single product entry.

**Expected RAG/Vector Behavior:** Should handle this easily with direct semantic match.

**Notes:** Baseline test to ensure basic functionality works correctly.

---

### Query 3.2: Tricky Bundled Purchase
**Question:** "If I buy both the Apple iPhone 15 Pro Max and the Nike Air Zoom Pegasus 40 together, what is the combined shipping weight, and will the vendor provide a bundled warranty for both items?"

**Answer:**
- The document lists separate shipping weights (iPhone: 221 grams; Nike Pegasus: 283 grams per shoe) but does not provide a combined shipping weight or details about bundled purchases
- Warranty information and bundled vendor policies are not specified
- Answer: "Combined weight would be 504 grams for iPhone + one shoe, but no bundled warranty information is found in the document"

**Reason for Difficulty:** Requires arithmetic across products, recognition of missing bundling policies, and clear statement of information gaps.

**Expected RAG/Vector Behavior:** May provide weights separately, struggle with addition, or incorrectly infer bundle policies that don't exist.

**Notes:** Tests multi-product reasoning and gap acknowledgment.

---

## Category 4: Certification and Compliance

### Query 4.1: Third-Party Certification
**Question:** "Which products in the catalog are certified by third-party organizations, and which organizations are involved in their certification?"

**Answer:** The CardioHealth Plus Daily Supplement is third-party tested, made in an FDA-registered facility, and has NSF International certification as well as a USP Verified quality seal.

**Reason for Difficulty:** Requires identifying certification-related information across product descriptions.

**Expected RAG/Vector Behavior:** Should retrieve this with semantic matching on certification keywords.

**Notes:** Tests ability to extract compliance and regulatory information.

---

### Query 4.2: Institutional Partners
**Question:** "Who is the institutional partner for the book titled 'The Future of Artificial Intelligence' and what is the publisher's distribution partner?"

**Answer:** The institutional partner is the Stanford AI Lab, and the publisher's distribution partner is MIT Press.

**Reason for Difficulty:** Requires distinguishing between different types of organizational relationships.

**Expected RAG/Vector Behavior:** May confuse different partner roles or merge them incorrectly.

**Notes:** Tests entity role disambiguation.

---

## Category 5: Temporal and Date-Based Reasoning

### Query 5.1: Expiration Date Identification
**Question:** "Which products have any information about expiration or best-before dates, and what are those dates?"

**Answer:** CardioHealth Plus Daily Supplement provides manufacturing (2024-01-15), expiration (2026-12-31), and best before (2026-12-31) dates.

**Reason for Difficulty:** Requires scanning all products for temporal information.

**Expected RAG/Vector Behavior:** Should handle with date-related semantic search.

**Notes:** Tests temporal information extraction.

---

### Query 5.2: Payment Terms and Due Dates
**Question:** "For any invoice with net payment terms, what is the due date and current payment status?"

**Answer:**
- Medical Equipment Invoice: Payment Status Net 30 - Due 2024-03-30
- Construction Materials Invoice: Payment Status Pending – Due 2024-04-09

**Reason for Difficulty:** Requires filtering invoices by payment term type and extracting related dates.

**Expected RAG/Vector Behavior:** Should retrieve with filtering on payment terms.

**Notes:** Tests conditional filtering and date extraction.

---

## Category 6: Multi-Category Comparison

### Query 6.1: Food-Service Equipment Comparison
**Question:** "List and compare all the food-service equipment ordered for a restaurant, including main technical specs and purchase prices."

**Answer:**
- Hobart Commercial Dishwasher: $8,999.00, High-temp sanitizing, 40 racks/hour, Energy Star, 24.5x25x34 inches
- Vulcan Gas Range: $5,499.00, 10 burners, 2 ovens, 300,000 BTU, 60" wide, Stainless Steel
- True Refrigerator: $3,299.00, 54x31x83 inches, Stainless Steel

**Reason for Difficulty:** Requires identifying category membership and aggregating specifications in comparative format.

**Expected RAG/Vector Behavior:** May retrieve items separately without structured comparison.

**Notes:** Tests categorical grouping and comparative presentation.

---

## Category 7: Advanced Logical Reasoning

### Query 7.1: Implicit Negative Logic
**Question:** "Which product listed in any invoice is not paid, and which vendor is responsible for it?"

**Answer:** The Construction Materials Invoice (Vendor: BuildRight Materials Supply) has Payment Status: Pending – Due 2024-04-09; those products (lumber, concrete mix, nails, paint) are not yet paid.fix

**Reason for Difficulty:** Requires understanding negative conditions (NOT paid) and mapping to vendors.

**Expected RAG/Vector Behavior:** Struggles with negative logic and may return all payment statuses without proper filtering.

**Notes:** Tests negative condition reasoning and cross-field mapping.

---

### Query 7.2: Unit Conversion and Arithmetic
**Question:** "What is the total combined weight of one True Refrigerator and two Air Zoom Pegasus 40 shoes, in kilograms?"

**Answer:**
- Nike Air Zoom Pegasus 40: 283 grams per shoe × 2 = 566 grams = 0.566 kg
- True Refrigerator: No explicit weight listed in the document
- Combined weight cannot be completed because the True Refrigerator weight is not specified; Nike shoes together weigh 0.566 kg

**Reason for Difficulty:** Requires arithmetic, unit conversion, and acknowledgment of missing data.

**Expected RAG/Vector Behavior:** May struggle with math operations and unit conversions, or fail to acknowledge missing data.

**Notes:** Tests mathematical reasoning and data gap recognition.

---

### Query 7.3: Hypothetical Timeline Simulation
**Question:** "If the construction materials order is delayed by 30 days past its due date, which other invoice will then have a later due date?"

**Answer:**
- Construction Materials Invoice due date: 2024-04-09; with 30-day delay: 2024-05-09
- No other listed invoice has a later due date
- After the delay, this invoice would have the latest due date of all invoices

**Reason for Difficulty:** Requires hypothetical date arithmetic and cross-invoice comparison.

**Expected RAG/Vector Behavior:** Struggles with hypothetical scenarios and date comparisons.

**Notes:** Tests scenario simulation and comparative temporal reasoning.

---

### Query 7.4: Multi-Hop Warranty Journey
**Question:** "For each product with a warranty, list the warranty term and identify the next related service (e.g., repair, return) process outlined—if any."

**Answer:** No warranty terms or related after-sale service processes are described for any product listed in the document.

**Reason for Difficulty:** Requires multi-step traversal through product → warranty → follow-up service.

**Expected RAG/Vector Behavior:** May hallucinate warranty information or fail to confirm absence.

**Notes:** Tests multi-hop reasoning and service process linkage.

---

### Query 7.5: Ambiguous Entity Matching
**Question:** "Which items ordered from a vendor with 'Tech' in their company name require delivery outside of the technology category?"

**Answer:**
- Vendors with "Tech": TechSupply Solutions (technology) and MedTech Equipment Supply (medical equipment)
- MedTech Equipment Supply provides medical devices, which is outside the technology category
- Items: Philips IntelliVue MX40 Patient Monitor, Welch Allyn Blood Pressure Cuff Set, Nonin Pulse Oximeter

**Reason for Difficulty:** Requires partial string matching and category exclusion logic.

**Expected RAG/Vector Behavior:** May use simple string matching and miss categorical context.

**Notes:** Tests fuzzy matching with logical constraints.

---

### Query 7.6: International/Cross-Language
**Question:** "Provide the payment terms explanation in both French and English for any invoice involving international shipment."

**Answer:** No payment terms related to international shipment are specified in the document.

**Reason for Difficulty:** Tests multi-language capability and conditional retrieval.

**Expected RAG/Vector Behavior:** May attempt translation without confirming condition exists.

**Notes:** Tests language versatility and conditional logic.

---

### Query 7.7: Manufacturer vs Vendor Relationship
**Question:** "List all products whose manufacturer is not the same as the listed vendor—and summarize each instance briefly."

**Answer:**
- Dell XPS 15 Laptop: Manufacturer Dell; Vendor TechSupply Solutions
- Michelin Pilot Sport 4S: Manufacturer Michelin North America; Vendor differs
- Philips IntelliVue: Manufacturer Philips Healthcare; Vendor MedTech Equipment Supply
- CardioHealth Plus Supplement: Manufacturer VitaLife Laboratories Inc.; Vendor VitaLife Sciences
- Hobart Commercial Dishwasher: Manufacturer Hobart Corporation; Vendor ChefPro Restaurant Supply Co.
- Summary: These products are supplied through third-party vendors, not their manufacturers

**Reason for Difficulty:** Requires field-level relationship cross-checking across all products.

**Expected RAG/Vector Behavior:** Struggles with relationship graph understanding and entity role comparison.

**Notes:** Tests deep relationship inference and entity role disambiguation.

---

## Summary of Test Categories

| Category | Query Count | Primary Challenge |
|----------|-------------|-------------------|
| Cross-Section Synthesis | 3 | Multi-document reasoning and similarity detection |
| Negative/Not-Found | 1 | Hallucination prevention and factual accuracy |
| Standard Ecommerce | 2 | Basic and complex product queries |
| Certification & Compliance | 2 | Regulatory information extraction |
| Temporal Reasoning | 2 | Date extraction and payment term logic |
| Multi-Category Comparison | 1 | Categorical grouping and comparison |
| Advanced Logic | 7 | Negative logic, math, scenarios, multi-hop, fuzzy matching, relationships |

**Total Queries:** 18

---

## Expected System Behavior Patterns

### Strengths (Most RAG/Vector Systems)
- Direct fact retrieval from single sections
- Keyword and semantic matching
- Basic product information lookup

### Weaknesses (Most RAG/Vector Systems)
- Cross-section synthesis and comparison
- Negative assertions ("not found" confidence)
- Mathematical operations and unit conversions
- Multi-hop logical reasoning
- Hypothetical scenario simulation
- Deep relationship graph traversal
- Ambiguous entity disambiguation
- Comprehensive aggregation across document sections

---

## Document Purpose
This test matrix serves as a comprehensive evaluation framework for:
1. Assessing RAG system capabilities and limitations
2. Benchmarking vector search semantic understanding
3. Identifying areas requiring enhanced context awareness
4. Testing real-world SaaS query complexity
5. Evaluating hallucination prevention mechanisms