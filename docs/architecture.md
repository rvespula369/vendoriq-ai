# VendorIQ v0.2 Architecture

## Processing pipeline

```text
User
  |
  v
Supplier URL + procurement requirement
  |
  +------------------------------+
  |                              |
  v                              v
Website crawler              Requirement parser
  |                              |
  v                              v
Query-aware normalization     Category / material /
  |                           specification / variant
  v                              |
Relevant-page ranking            |
  |                              |
  v                              |
Content cleaning                 |
  |                              |
  v                              |
LLM structured extraction        |
  |                              |
  v                              |
Pydantic validation              |
  |                              |
  +--------------+---------------+
                 |
                 v
       Deterministic verifier
                 |
                 v
       Explainable scoring
                 |
                 v
      Evidence-aware report
```

## Separation of responsibilities

### Deterministic Python
- URL canonicalization and query preservation
- same-domain filtering
- page deduplication
- page ranking
- requirement decomposition
- exact/normalized technical matching
- score calculation
- report formatting

### LLM
- interpret unstructured company website text
- normalize supplier/product facts
- separate technical capabilities from marketing/company claims
- classify certification/approval records
- identify missing information and explicit risks without inventing facts

## Safety / quality rules

1. Missing evidence is recorded as unverified, not as a negative finding.
2. Scraped website content is treated as untrusted data.
3. Important facts include source URLs where available.
4. The LLM cannot directly set the supplier score.
5. Exact procurement attributes such as size and design variant are checked independently from product-family relevance.
6. Human verification remains mandatory for supplier qualification.
