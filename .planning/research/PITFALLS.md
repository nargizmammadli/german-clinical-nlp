# Domain Pitfalls

**Domain:** German Clinical NLP Information Extraction
**Researched:** 2026-06-11
**Confidence:** HIGH

---

## Critical Pitfalls

Mistakes that cause rewrites, data quality failures, or deployment failures.

### Pitfall 1: Negation Scope Misidentification

**What goes wrong:** The system extracts "pneumonia" as a positive finding from "no evidence of pneumonia" or incorrectly marks "patient denies chest pain" as affirming chest pain. Almost half of false positives in rule-based negation detection fall under the "scope" category.

**Why it happens:** Default negation scope extends to sentence boundaries. In long sentences or poorly segmented text, a single negation trigger (e.g., "no", "kein", "nicht") falsely modifies many medical terms far from the trigger. German's flexible word order and complex negation constructions ("weder...noch", "nicht...sondern") exacerbate the problem.

**Consequences:**
- False positives: Extracting conditions the patient does NOT have
- Clinical safety risk: Downstream systems may treat denied symptoms as confirmed
- Low precision: Pipeline appears to work but produces unreliable extractions
- Loss of trust: Reviewers see obvious errors, question entire system

**Prevention:**
1. **Restrict negation scope** to fixed token windows (e.g., 5-7 tokens) rather than sentence boundaries
2. **Add termination triggers** that end negation scope early (e.g., "but", "jedoch", "allerdings")
3. **Use dependency parsing** (e.g., Stanford dependency parser via DEEPEN algorithm) to identify syntactic relationships between negation words and entities
4. **Validate with German-specific patterns** for compound negations ("weder...noch") and modal constructions ("könnte nicht")
5. **Test with adversarial examples** containing multiple entities after negation triggers

**Detection:** 
- Review extraction output for sentences with negation words ("kein", "nicht", "ohne", "negativ")
- Calculate precision/recall specifically for negated vs affirmed entities
- Manual spot-check of long sentences (>15 tokens) with negation triggers

**Phase mapping:** Phase 1 (Core extraction) must include negation handling, not deferred to later phases.

**Sources:**
- [Negation detection in Dutch clinical texts](https://arxiv.org/pdf/2209.00470)
- [DEEPEN: A negation detection system for clinical text](https://pmc.ncbi.nlm.nih.gov/articles/PMC5863758/)
- [Negation Scope Detection in Clinical Notes and Scientific Abstracts](https://pmc.ncbi.nlm.nih.gov/articles/PMC6568093/)

---

### Pitfall 2: German Compound Word Tokenization Failures

**What goes wrong:** The model fails to recognize "Niereninsuffizienz" (renal insufficiency) as a medical condition, or splits it incorrectly. Multi-level semantic annotations are lost—"Niereninsuffizienz" refers to both a BODY_PART ("Nieren" = kidney) and MEDICAL_CONDITION, but only the compound captures the actual diagnosis.

**Why it happens:** German writes compound nouns without spaces (e.g., "Computerlinguistik", "Lebensversicherungsgesellschaftsangestellter"). Standard whitespace tokenization treats these as single unknown tokens. Medical terminology contains extensive compounds ("Herzinsuffizienztherapie", "Lungenemboliediagnose"). LLM tokenizers may split compounds at arbitrary subword boundaries, breaking semantic units.

**Consequences:**
- **Low recall:** Missing critical diagnoses because compounds aren't recognized
- **Boundary errors:** Extracting "Nieren" (kidney) instead of "Niereninsuffizienz" (renal insufficiency)
- **Dictionary lookup failures:** Compound not in UMLS/vocabulary, even though components are
- **Context loss:** Breaking "Niereninsuffizienz" loses the relationship between kidney and insufficiency

**Prevention:**
1. **Choose models with German-aware tokenization** (e.g., GBERT, GottBERT, or German medical-specific models like those tested on GGPONC)
2. **Pre-process with compound splitters** if using English-dominant models, but preserve original compounds for entity boundaries
3. **Use subword tokenization methods** (BPE, WordPiece) that handle rare compounds via component pieces
4. **Validate entity boundaries** to ensure extracted spans align with full compound words, not fragments
5. **Build test suite** with common German medical compounds from GGPONC/BRONCO datasets

**Detection:**
- Track extraction recall on known compound entities
- Monitor extractions for partial words (e.g., "Nieren" alone without "insuffizienz")
- Compare tokenizer output on medical compounds vs expected segmentation

**Phase mapping:** Address in Phase 1 (model selection and prompt engineering). Tokenization issues cascade through entire pipeline.

**Sources:**
- [GERNERMED++: Semantic annotation in German medical NLP](https://www.sciencedirect.com/science/article/pii/S1532046423002344)
- [A Medical Information Extraction Workbench to Process German Clinical Text](https://arxiv.org/pdf/2207.03885)
- [GGPONC: A Corpus of German Medical Text](https://arxiv.org/pdf/2007.06400)

---

### Pitfall 3: LLM Hallucination Without Detection

**What goes wrong:** The model confidently outputs "Patient diagnosed with diabetes mellitus on 2025-03-15" when the input text says "diabetes screening scheduled for March". Or extracts medications never mentioned in the note. Hallucinations in clinical NLP use domain-specific terminology and appear coherent, making them hard to detect without expert review.

**Why it happens:** LLMs generate plausible-sounding text based on patterns, not facts. In extraction tasks, the model may "fill in" expected fields even when source text lacks that information. Structured output schemas create pressure to populate all fields. Medical LLMs trained on clinical literature may generate textbook diagnoses not present in the actual note.

**Consequences:**
- **Patient safety risk:** Fabricated diagnoses or medications could inform clinical decisions
- **Loss of trust:** One detected hallucination undermines confidence in all outputs
- **Regulatory/compliance issues:** Inaccurate medical records violate healthcare standards
- **Silent failures:** Hallucinations look correct without ground truth comparison

**Prevention:**
1. **Implement grounding verification:** Cross-reference every extracted entity against input text character spans
2. **Require text evidence:** Schema should include `source_span` or `evidence_text` fields showing where entity was found
3. **Use confidence thresholds:** Flag extractions below 0.7 confidence for human review
4. **Constrained decoding:** Use grammar-based decoding or JSON schema enforcement to prevent free-form generation
5. **Prompt engineering:** Explicitly instruct "Extract ONLY information present in the text. If not mentioned, return null"
6. **Validation rules:** Pydantic validators should reject impossible values (future dates, medications not in formulary)
7. **Dual-LLM verification:** Secondary model verifies extraction against source (LLM-as-judge pattern)

**Detection:**
- **Manual audit:** Sample 50-100 extractions, verify each field against source text
- **Automated checks:** Flag extractions where entity text doesn't appear in source (fuzzy match allowing for synonyms)
- **Statistical anomalies:** Unusually high extraction counts (e.g., every note has 5+ diagnoses) suggest over-extraction
- **User feedback:** Provide mechanism for domain experts to flag hallucinated extractions

**Phase mapping:** Must address in Phase 1 core pipeline. Hallucination detection is foundational, not optional.

**Sources:**
- [Medical Hallucination in Foundation Models](https://www.medrxiv.org/content/10.1101/2025.02.28.25323115v2.full.pdf)
- [A framework to assess clinical safety and hallucination rates of LLMs](https://www.nature.com/articles/s41746-025-01670-7)
- [A Scoping Review of Natural Language Processing in Addressing Medically Inaccurate Information](https://arxiv.org/pdf/2505.00008)

---

### Pitfall 4: Context Window Truncation Losing Critical Information

**What goes wrong:** A long discharge summary (3000+ tokens) gets truncated at the model's context window limit. The medication list appears in the truncated section—the extraction returns zero medications when the note actually lists five. Or temporal sequencing is lost because early events fall outside the window.

**Why it happens:** Clinical documents routinely exceed 2K-8K tokens. Smaller GGUF models often have 2K-4K context windows. LLMs exhibit "lost in the middle" problem—even with larger context windows, they focus on beginning/end of input and neglect middle sections. Naive truncation strategies (e.g., take first N tokens) discard valuable information.

**Consequences:**
- **Low recall:** Missing entities in truncated sections
- **Temporal incoherence:** Events out of order if early history is truncated
- **Silent failures:** System doesn't indicate that input was truncated
- **Biased extraction:** Over-represents information at document start

**Prevention:**
1. **Choose models with adequate context windows:** For clinical notes, 8K+ token context preferred (e.g., Llama 3 8K, Mistral 8K)
2. **Document-aware chunking:** Split on section headers (Anamnese, Diagnosen, Medikation) rather than arbitrary token limits
3. **Sliding window with aggregation:** Process document in overlapping chunks, merge extractions with deduplication
4. **Extractive pre-summarization:** Use NER-based method to identify relevant sections before feeding to LLM
5. **Multi-pass extraction:** First pass identifies entity locations, second pass extracts details from targeted sections
6. **Validate input length:** Log warnings when input approaches context limit, flag outputs as potentially incomplete

**Detection:**
- Monitor input token lengths vs model context window
- Track extraction counts by input length (if longer notes consistently yield fewer entities, suspect truncation)
- Test with known long documents containing entities throughout (ensure later entities are captured)

**Phase mapping:** Address in Phase 1 (model selection) and Phase 2 (chunking strategy if needed). Document preprocessing precedes extraction.

**Sources:**
- [Context Window Limits: Why Your LLM Still Hallucinates](https://pr-peri.github.io/llm/2026/02/13/why-hallucination-happens.html)
- [Strategies and Techniques for Managing the Size of the Context Window](https://mohdmus99.medium.com/strategies-and-techniques-for-managing-the-size-of-the-context-window-when-using-llm-large-3c2dbc5dcc3a)
- [Improving Clinical Trial Recruitment using Clinical Narratives and Large Language Models](https://arxiv.org/pdf/2604.05190)

---

### Pitfall 5: Unreliable Confidence Scores

**What goes wrong:** The model assigns 0.95 confidence to a hallucinated diagnosis and 0.60 confidence to a correctly extracted medication. You implement a 0.70 threshold expecting to filter low-quality extractions, but it filters valid entities and keeps hallucinations. Downstream automation trusts high-confidence scores that are poorly calibrated.

**Why it happens:** LLMs are inherently overconfident. Training on clinical data doesn't guarantee well-calibrated confidence scores. Softmax probabilities from token generation ≠ reliability of extraction. Model may be confident in its generation while being factually wrong. Generic LLMs lack calibration for medical domain.

**Consequences:**
- **False sense of reliability:** High confidence scores mislead users into trusting incorrect extractions
- **Broken automation:** Thresholds based on confidence fail to separate good/bad extractions
- **Missed errors:** Overconfident hallucinations bypass manual review
- **Poor risk stratification:** Can't reliably route uncertain cases to human experts

**Prevention:**
1. **Don't trust raw confidence scores:** Treat them as uncalibrated heuristics, not ground truth
2. **Calibrate on validation set:** Map model scores to actual accuracy using temperature scaling or isotonic regression
3. **Use multiple confidence signals:**
   - Token-level probabilities
   - Entity extraction probability
   - Evidence strength (how well entity matches source text)
   - Consistency (does re-running with different temperature yield same entity?)
4. **Ensemble verification:** Run extraction with multiple prompts/models, flag disagreements as uncertain
5. **Confidence-aware evaluation:** Measure Expected Calibration Error (ECE) and Brier Score on validation set
6. **Human-in-loop for uncertainty:** Route low-confidence AND high-confidence-but-suspicious extractions for review

**Detection:**
- Calculate calibration metrics (ECE, Brier Score) on labeled validation set
- Plot reliability diagrams (predicted confidence vs actual accuracy)
- Audit high-confidence errors (model score >0.8 but extraction is wrong)

**Phase mapping:** Address in Phase 2-3 (after core extraction works). Requires labeled validation data to calibrate.

**Sources:**
- [Mind the Gap: Benchmarking LLM Uncertainty, Discrimination, and Calibration](https://arxiv.org/html/2506.10769v2)
- [When Can We Trust LLM Graders? Calibrating Confidence for Automated Assessment](https://arxiv.org/pdf/2603.29559)
- [A Study of Calibration as a Measurement of Trustworthiness of Large Language Models](https://www.biorxiv.org/content/10.1101/2025.02.11.637373.full.pdf)

---

### Pitfall 6: Docker Memory Errors with GGUF Models

**What goes wrong:** Docker container fails with OOM (Out of Memory) during model loading, or the container starts but crashes within 10 seconds with "error loading model: failed to mmap file". Production deployment works locally but fails in containerized environment with identical resource limits.

**Why it happens:** GGUF models require significant RAM just to load (e.g., 70B Q4_K_M needs ~40GB RAM + overhead for KV cache). Docker default memory limits (often 2GB) are insufficient. File permission issues prevent mmap from loading model files. Recent llama.cpp versions may have regressions (e.g., v0.3.2+ stopped using CPU offload properly, causing OOM when model doesn't fit in VRAM).

**Consequences:**
- **Deployment failure:** Container won't start or crashes immediately
- **Silent crashes:** ~40% of llama.cpp production incidents involve silent crash within first 10 seconds
- **Resource waste:** Container reserves memory but can't use it
- **Delayed detection:** Works in development, fails in production with restricted resources

**Prevention:**
1. **Calculate memory requirements:** Model size + 2-4GB overhead + KV cache (depends on context window)
2. **Set explicit Docker memory limits:** 
   ```dockerfile
   # For 8B Q4 model (~5GB) + 3GB overhead
   docker run --memory="8g" --memory-swap="8g" ...
   ```
3. **Use appropriate quantization:** Q4_K_M for development, Q3_K_M if memory-constrained (~25% smaller)
4. **Test with realistic resource limits:** Don't develop with unlimited memory if production has constraints
5. **Fix file permissions:** Ensure model files are owned by UID 0 or add `:z` SELinux label in volume mount
   ```bash
   docker run -v ./models:/models:z ...
   ```
6. **Monitor during startup:** Add health checks that detect early crashes
7. **Pin llama.cpp version:** Recent versions have regressions; test before upgrading

**Detection:**
- Monitor container startup logs for "failed to mmap", "out of memory", "device lost" errors
- Use `docker stats` to track memory usage during model loading
- Implement startup health check that fails if model isn't loaded within 30s
- Test container with `--memory` flag matching production limits

**Phase mapping:** Must address in Phase 3 (Docker packaging). Test containerized deployment early, not at the end.

**Sources:**
- [Bug: Excess system memory usage during GGUF loading](https://github.com/vllm-project/vllm/issues/22814)
- [Docker with llama.cpp — Production Integration Guide](https://markaicode.com/integrate/docker-with-llamacpp/)
- [Fix llama.cpp Connection Refused: 3-Minute Production Fix](https://markaicode.com/errors/llamacpp-connection-refused-fix-production/)

---

## Moderate Pitfalls

Mistakes that cause reduced accuracy or require significant rework.

### Pitfall 7: Ambiguous Abbreviation Expansion Errors

**What goes wrong:** The system expands "ER" as "Emergency Room" when the context indicates "Estrogen Receptor" in an oncology note. Or fails to expand "MVI" (Multi-Vitamins) because the abbreviation isn't in the knowledge base. Abbreviations constitute 30-50% of clinical text vs <1% in general text, and many are ambiguous (e.g., "ER" has 3+ medical meanings).

**Why it happens:** Clinical notes use abbreviations extensively without definitions. Same abbreviation has multiple meanings depending on context (radiology vs cardiology vs oncology). Knowledge bases are incomplete—many abbreviations don't exist in standard dictionaries. Context window may not capture enough information to disambiguate.

**Consequences:**
- Incorrect entity extraction: Extracting wrong diagnosis based on mis-expanded abbreviation
- Missed entities: Unrecognized abbreviations aren't extracted
- Low recall: ~54% of incorrect expansions are due to low semantic similarity (insufficient training data)

**Prevention:**
1. **Use domain-specific abbreviation dictionaries** for German medical text
2. **Context-aware expansion:** Use sentence/paragraph context to disambiguate (e.g., BERT-based disambiguation)
3. **Preserve original abbreviations:** Extract "ER" as-is, include abbreviation expansion as separate field with confidence
4. **Few-shot prompting:** Provide examples of abbreviation expansions in the clinical specialty of interest
5. **Flag uncertain expansions:** If multiple meanings possible, return list of candidates with probabilities

**Detection:**
- Manual review of extracted abbreviations vs source text
- Track extraction accuracy specifically for notes with high abbreviation density
- Maintain list of known ambiguous abbreviations, audit those extractions

**Phase mapping:** Address in Phase 2 (entity normalization). Initial extraction can preserve abbreviations, expansion is refinement step.

**Sources:**
- [Unsupervised Abbreviation Expansion in Clinical Narratives](https://www.researchgate.net/publication/322252710_Unsupervised_Abbreviation_Expansion_in_Clinical_Narratives)
- [A deep database of medical abbreviations and acronyms for NLP](https://www.nature.com/articles/s41597-021-00929-4)
- [Disambiguating Clinical Abbreviations](https://medinform.jmir.org/2024/1/e56955)

---

### Pitfall 8: Temporal Expression Ambiguity

**What goes wrong:** The system extracts "the night prior" but can't determine the actual date. Or "the day prior to admission" fails to resolve because admission date appears elsewhere in document. Copy-pasted notes from multiple visits create inconsistent temporal references ("today" refers to different dates in different sections).

**Why it happens:** Clinical text uses implicit, relative temporal expressions ("several weeks ago", "that time", "before admission"). Date formats vary (DD.MM.YYYY in German text vs MM/DD/YYYY in some EHR systems). Temporal references depend on context (admission date, note creation date) that may be in metadata, not text. Typos and redundant text obscure actual dates.

**Consequences:**
- Incorrect timeline: Events assigned to wrong dates
- Missing temporal information: Relative dates not normalized to absolute dates
- Inconsistent inferences: Copy-pasted text creates contradictory date references

**Prevention:**
1. **Extract document metadata:** Admission date, discharge date, note creation date as anchors for relative dates
2. **Normalize temporal expressions:** Convert "2 weeks ago" to absolute date using note creation date
3. **Flag ambiguous expressions:** "that time", "several weeks" marked as LOW confidence with imprecise normalization
4. **Validate date logic:** Ensure discharge date > admission date, treatment dates within admission period
5. **Prompt for explicit dates:** Instruct model to prefer explicit dates over ambiguous references
6. **Use ISO 8601 standard:** Normalize all dates to YYYY-MM-DD format in output

**Detection:**
- Review extractions for relative date expressions without normalization
- Validate that normalized dates fall within reasonable ranges (not 50 years ago for acute care)
- Check for impossible date sequences (treatment before diagnosis)

**Phase mapping:** Address in Phase 1-2 (extraction and normalization). Date validation critical for clinical timelines.

**Sources:**
- [Extraction of Temporal Information from Clinical Narratives](https://pmc.ncbi.nlm.nih.gov/articles/PMC8982722/)
- [MedTime: A Temporal Information Extraction System](https://www.researchgate.net/publication/255176435_MedTime_A_Temporal_Information_Extraction_System_for_Clinical_Narratives)
- [Towards generating a patient's timeline](https://pmc.ncbi.nlm.nih.gov/articles/PMC3974721/)

---

### Pitfall 9: Medication Dosage/Strength Confusion

**What goes wrong:** The system extracts "500 mg" as the strength when it's actually the dosage. For "Meropenem 500 mg Intravenous every eight hours," the 500 mg is labeled as strength instead of dosage. Frequency expressions like "two times a day" vs "b.i.d" aren't normalized, causing duplicate or missed extractions.

**Why it happens:** Dosage and strength are both numeric quantities in similar contexts—models confuse them. Medication information in clinical text is unstructured, with inconsistent ordering. Frequency expressions have many equivalent forms that need normalization. Knowledge bases may not contain all medication names, abbreviations, or misspellings.

**Consequences:**
- Incorrect medication records: Wrong dosage can have patient safety implications
- Failed normalization: Same medication with different frequency formats not de-duplicated
- Low recall: Unrecognized medication abbreviations (e.g., "MVI" for Multi-Vitamins) missed

**Prevention:**
1. **Use structured extraction schema:** Separate fields for medication name, strength, dosage, route, frequency
2. **Define clear field semantics in prompt:** "Strength is the concentration (e.g., 500mg/tablet). Dosage is amount taken (e.g., 500mg per dose)."
3. **Normalize frequency:** Convert all forms to standard (e.g., "BID", "twice daily", "two times a day" → "2x/day")
4. **Validate units:** mg, mcg, mL, units, IU with conversion factors
5. **Use medication knowledge base:** RxNorm, ATC codes for normalization and validation
6. **Test with complex medication orders:** Multi-drug regimens, tapered dosages, PRN medications

**Detection:**
- Review dosage/strength assignments for numeric values
- Check if frequency normalization consolidates equivalent expressions
- Validate medication names against formulary or RxNorm

**Phase mapping:** Address in Phase 2 (detailed entity extraction with attributes). Simple name extraction in Phase 1, detailed attributes in Phase 2.

**Sources:**
- [Extracting and standardizing medication information – the MedEx-UIMA system](https://pmc.ncbi.nlm.nih.gov/articles/PMC4419757/)
- [Extracting Drug Names and Associated Attributes From Discharge Summaries](https://medinform.jmir.org/2021/5/e24678)
- [MedXN: an open source medication extraction and normalization tool](https://pmc.ncbi.nlm.nih.gov/articles/PMC4147619/)

---

### Pitfall 10: Limited German Medical Resource Coverage

**What goes wrong:** The German UMLS contains only ~234k entries vs 6.5M in English UMLS. Dictionary-based entity linking fails because German medical terms aren't in the knowledge base. Gene extraction produces many false positives because common German words match gene names (three-letter acronyms collision).

**Why it happens:** German medical NLP resources are scarce compared to English. UMLS and other medical ontologies are English-centric. Translation-based approaches introduce errors with ambiguous or domain-specific terms. Publicly available German medical NER models are limited.

**Consequences:**
- Low recall in entity linking: Can't map extracted entities to standard codes (ICD-10, SNOMED CT)
- False positives: Common German words incorrectly identified as medical entities
- Dependency on translation: Translating German→English→extraction→German introduces errors

**Prevention:**
1. **Use German-specific medical resources:** GGPONC, BRONCO datasets for training/validation
2. **Fine-tune on German medical text:** Models like GottBERT, German BERT, or medical-specific German LLMs
3. **Hybrid approach:** Extraction on German text, then entity linking with translated terms + manual mapping
4. **Build custom terminology list:** Compile German medical terms from clinical guidelines (e.g., GGPONC oncology guidelines)
5. **Validate with German medical experts:** Ensure extracted entities match German clinical language conventions

**Detection:**
- Track entity linking success rate (what % of extracted entities map to codes)
- Monitor false positives in gene/acronym extraction
- Review extraction output for language mixing (German text with English entity labels)

**Phase mapping:** Address in Phase 1 (model selection—choose German-aware models). Entity linking/normalization in Phase 2-3.

**Sources:**
- [How to improve information extraction from German medical records](https://www.researchgate.net/publication/309278662_How_to_improve_information_extraction_from_German_medical_records)
- [GERNERMED++: Semantic annotation in German medical NLP](https://www.sciencedirect.com/science/article/pii/S1532046423002344)
- [GGPONC: A Corpus of German Medical Text](https://arxiv.org/pdf/2007.06400)

---

## Minor Pitfalls

Common issues that are easily fixed or have limited impact.

### Pitfall 11: JSON Schema Violations in LLM Output

**What goes wrong:** The model returns JSON with extra prose (`"Here is the extraction: {... }"`), wrong field names, unexpected fields, or syntactically invalid JSON (missing quotes, trailing commas).

**Why it happens:** LLMs generate text, not structured data. Even with JSON mode enabled, the model may add narrative around the JSON. Schema adherence isn't guaranteed—model may invent field names or omit required fields.

**Consequences:**
- Parsing errors: Invalid JSON crashes the parser
- Validation failures: Extra fields or wrong types fail Pydantic validation
- Need for post-processing: Extracting JSON from prose adds complexity

**Prevention:**
1. **Use strict JSON mode:** OpenAI-compatible APIs have `response_format: {type: "json_object"}`
2. **Enforce schema with constrained decoding:** Grammar-based decoding (e.g., llama.cpp JSON schema enforcement)
3. **Validate with Pydantic:** Define strict schema, reject responses that don't conform
4. **Set low temperature:** 0.0-0.1 reduces randomness and format drift
5. **Retry with error feedback:** If validation fails, retry with error message in prompt
6. **Strip prose:** Pre-process response to extract JSON block (strip text before `{` and after `}`)

**Detection:**
- Monitor JSON parsing errors in logs
- Track Pydantic validation failure rate
- Review failed responses for common format violations

**Phase mapping:** Address in Phase 1 (prompt engineering and response parsing). Foundational for reliable structured output.

**Sources:**
- [Structured Output From LLMs: 288 Calls Logged](https://dasroot.net/posts/2026/05/structured-output-llms-json-breaks-analyzed/)
- [How To Ensure LLM Output Adheres to a JSON Schema](https://modelmetry.com/blog/how-to-ensure-llm-output-adheres-to-a-json-schema)
- [JSON for LLMs: Complete Guide to Structured Outputs](https://superjson.ai/blog/2025-08-17-json-schema-structured-output-apis-complete-guide/)

---

### Pitfall 12: Inadequate Health Check Implementation

**What goes wrong:** The `/health` endpoint always returns 200 OK, even when the model fails to load or dependencies are unavailable. Kubernetes restarts containers unnecessarily, or doesn't restart when the model crashes. Monitoring systems can't distinguish between "server running" and "server can actually process requests."

**Why it happens:** Simple health checks only verify HTTP server responds, not that dependencies work. Developers conflate liveness (is process alive?) with readiness (can it handle requests?). Health checks don't test actual model inference. Slow or blocking health checks cause timeouts.

**Consequences:**
- False positives: Health check passes but extraction fails
- Unnecessary restarts: Slow health check causes timeouts, Kubernetes restarts healthy containers
- No visibility into degradation: Model loaded but running slowly, health check doesn't detect

**Prevention:**
1. **Separate liveness and readiness:**
   - `/live`: Fast, no dependencies, just returns 200 (is process alive?)
   - `/ready`: Checks model loaded, can process requests
2. **Test model inference in readiness:** Run lightweight extraction on sample input, verify output
3. **Include dependency status:** Check if GPU available (if used), sufficient memory
4. **Set appropriate timeouts:** Liveness <1s, readiness <5s
5. **Return 503 if not ready:** HTTP 503 Service Unavailable if model not loaded or dependencies failed
6. **Log health check failures:** Don't silently fail, log what's wrong

**Detection:**
- Test health endpoint after deployment (does it detect model loading failure?)
- Simulate failures (remove model file, exhaust memory) and verify health check catches them
- Monitor health check latency (if >1s for liveness, it's too slow)

**Phase mapping:** Address in Phase 3 (API implementation). Critical for reliable deployment.

**Sources:**
- [FastAPI Health Check Endpoint Example](https://www.index.dev/blog/how-to-implement-health-check-in-python)
- [Health Checks | FastAPI Production Guide](https://patrykgolabek.dev/guides/fastapi-production/health-checks/)
- [Implementing Health Checks and Auto-Restarts for FastAPI Applications](https://medium.com/@ntjegadeesh/implementing-health-checks-and-auto-restarts-for-fastapi-applications-using-docker-and-4245aab27ece)

---

### Pitfall 13: Testing Only on Synthetic Data

**What goes wrong:** Pipeline achieves 95% accuracy on synthetic clinical notes from LLM generation but fails miserably on real GGPONC/BRONCO samples. Synthetic data lacks the messiness of real clinical text—typos, abbreviations, incomplete sentences, copy-pasted boilerplate.

**Why it happens:** Synthetic data is cleaner and more consistent than real data. LLM-generated notes follow patterns the extraction model recognizes easily (both trained on similar distributions). Real clinical notes have domain-specific complexity: abbreviations, section headers, formatting inconsistencies, multi-lingual mixing (German + Latin terms).

**Consequences:**
- Overestimated performance: Synthetic validation set shows high accuracy, real-world performance is much lower
- Missed edge cases: Typos, rare abbreviations, formatting variations not in synthetic data
- Loss of trust: Portfolio demo works perfectly, but breaks on actual clinical text samples

**Prevention:**
1. **Use real German clinical datasets:** GGPONC (oncology guidelines) and BRONCO (discharge summaries)
2. **Mix synthetic and real data:** Synthetic for augmentation, real for validation
3. **Validate on held-out real data:** Final evaluation must include authentic clinical text
4. **Test on adversarial examples:** Intentionally messy notes with typos, abbreviations, mixed languages
5. **Document data sources:** Clearly state what data is synthetic vs real in README

**Detection:**
- Compare performance metrics on synthetic vs real validation sets
- Manual review of extraction errors on real data (do they reveal patterns not in synthetic data?)
- Test with samples from different clinical specialties (oncology, cardiology, etc.)

**Phase mapping:** Address in Phase 1-2 (validation dataset). Use synthetic for development, real for final validation.

**Sources:**
- [Synthetic data for annotation and extraction of family history](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8278746/)
- [SynthTextEval: Synthetic Text Data Generation and Evaluation](https://arxiv.org/pdf/2507.07229)
- [Enhancing and Not Replacing Clinical Expertise: Mixed Real–Synthetic Training](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12387308/)

---

### Pitfall 14: Ignoring Model Selection for German Performance

**What goes wrong:** You choose a popular English medical LLM (e.g., MedPaLM) or general multilingual model, but it performs poorly on German clinical text. The Qwen family of models is particularly weak in generating German text, often mixing German with Chinese/English despite claiming German support. Some models have 20-30% lower accuracy on German vs English medical questions.

**Why it happens:** Most medical LLMs are trained primarily on English biomedical literature. Multilingual models allocate capacity across many languages—German medical text gets less representation. Tokenizer inefficiencies: German compounds are split into more subword tokens than English equivalents, reducing effective context window. Some model families have known German generation quality issues.

**Consequences:**
- Low extraction accuracy on German text
- Language mixing: Output contains English or Chinese alongside German
- Suboptimal tokenization: German compounds inefficiently tokenized

**Prevention:**
1. **Benchmark German-specific performance:** Test candidate models on GGPONC samples before choosing
2. **Prefer German-aware models:**
   - GottBERT, GBERT for encoders
   - OpenBioLLM-8B (German support validated)
   - MedGemma-27B (strong German performance)
   - Avoid: Qwen family (known German generation issues)
3. **Test tokenization efficiency:** Compare token count for same German clinical text across models
4. **Use language-matched prompts:** Some models perform better with English prompts, others with German prompts—test both
5. **Check model documentation:** Verify German is officially supported with benchmarks, not just claimed

**Detection:**
- Evaluate extraction accuracy on German validation set (not English)
- Review output for language mixing (German entities with English labels, or vice versa)
- Compare tokenization: count tokens for same German clinical note across models

**Phase mapping:** Address in Phase 1 (model selection). Choosing the wrong model is costly to fix later.

**Sources:**
- [Why LLM Performance Drops in Non-English Languages](https://lilt.com/blog/multilingual-llm-performance-gap-analysis)
- [Performance Evaluation of Large Language Models in Multilingual Medical Questions](https://pmc.ncbi.nlm.nih.gov/articles/PMC12978932/)
- [Comprehensive Study on German Language Models for Clinical Text](https://arxiv.org/html/2404.05694)

---

### Pitfall 15: Non-Extensible Entity Type Architecture

**What goes wrong:** You hardcode extraction logic for dates, diagnoses, medications, and length-of-stay. Adding a new entity type (e.g., procedures, lab results) requires rewriting prompt templates, Pydantic schemas, parsing logic, and validation rules. For a portfolio project meant to showcase extensibility, the code is rigid.

**Why it happens:** Initial implementation focuses on getting extraction working for specified entity types. Entity-specific logic is duplicated across prompt, schema, and validation. No abstraction layer for entity type configuration.

**Consequences:**
- Difficult to demonstrate extensibility (a stated project goal)
- Code duplication across entity types
- Hard to add new entity types (requires touching multiple files)
- Doesn't showcase architectural thinking

**Prevention:**
1. **Use configuration-driven architecture:** JSON/YAML file defines entity types with extraction rules
2. **Plugin pattern:** Each entity type is a module with schema, validation, post-processing
3. **Generic extraction prompt:** Template accepts entity type definitions dynamically
4. **Pydantic schema generation:** Build schemas programmatically from entity type config
5. **Demonstrate extensibility in README:** Show adding a new entity type (e.g., "lab results") by adding config, not code

**Example config-driven approach:**
```yaml
entity_types:
  - name: diagnosis
    description: "Medical diagnosis or condition"
    examples: ["Pneumonie", "Diabetes mellitus Typ 2"]
    validators: [no_future_dates, icd10_format]
  - name: medication
    description: "Medication name and dosage"
    examples: ["Metformin 500mg", "Aspirin"]
    validators: [valid_dosage_units]
```

**Detection:**
- Try adding a new entity type—how many files need changes?
- Code review: Is entity type logic centralized or scattered?

**Phase mapping:** Design in Phase 1, implement in Phase 2-3. Refactoring late is expensive.

**Sources:**
- [A Lightweight API-Based Approach for Building Flexible Clinical NLP Systems](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6714318/)
- [Extracting Medical Named Entities with Healthcare NLP's EntityRulerInternal](https://www.johnsnowlabs.com/extracting-medical-named-entities-with-healthcare-nlps-entityrulerinternal/)

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| Model Selection (Phase 1) | Choosing English-optimized model or one with poor German support | Benchmark on GGPONC samples; prefer German medical models (OpenBioLLM-8B, MedGemma-27B) |
| Prompt Engineering (Phase 1) | Not addressing negation scope or compound word boundaries in prompts | Include explicit instructions for negation handling and entity boundaries; use few-shot examples with German compounds |
| Schema Design (Phase 1) | Missing source span / evidence fields, enabling hallucination | Require `evidence_text` or `source_span` in schema; validate extractions against input |
| Docker Packaging (Phase 3) | OOM during model loading or mmap failures | Calculate memory requirements; test with production-like limits; fix file permissions |
| Validation Dataset (Phase 2) | Only testing on synthetic data | Include real GGPONC/BRONCO samples in validation; document mix of synthetic/real |
| Confidence Scoring (Phase 2-3) | Trusting uncalibrated confidence scores | Calibrate on validation set; use multiple signals; don't automate based on raw scores |
| API Implementation (Phase 3) | Naive health check that doesn't test model | Separate liveness/readiness; test model inference in readiness check |
| Entity Extraction (Phase 1-2) | Context window truncation on long documents | Choose model with 8K+ context; implement chunking strategy; validate input length |
| Entity Normalization (Phase 2) | Abbreviation expansion errors | Use context-aware expansion; preserve original abbreviations; flag uncertain expansions |
| Temporal Extraction (Phase 2) | Ambiguous relative dates not normalized | Extract metadata (admission date); normalize relative expressions; flag imprecise dates |
| Medication Extraction (Phase 2) | Dosage/strength confusion | Separate schema fields; define clear semantics in prompt; normalize frequency |
| German Language Support (Phase 1) | Poor tokenization of compound words | Choose German-aware tokenizer; test on medical compounds; validate entity boundaries |
| Entity Linking (Phase 2-3) | Limited German UMLS coverage | Use GGPONC/BRONCO terminology; hybrid German extraction + translated linking |
| Structured Output (Phase 1) | JSON format violations | Use strict JSON mode; constrained decoding; low temperature; validate with Pydantic |
| Extensibility (Phase 1-2) | Hardcoded entity types, difficult to extend | Config-driven architecture; plugin pattern; demonstrate adding new entity type |

---

## Summary

The most critical pitfalls for this German clinical NLP extraction project are:

1. **Negation scope misidentification** — Leads to false positives in entity extraction, undermining trust
2. **German compound word tokenization failures** — Low recall on diagnoses if compounds not handled properly
3. **LLM hallucination without detection** — Patient safety risk; requires evidence grounding
4. **Context window truncation** — Silent loss of critical information in long clinical notes
5. **Unreliable confidence scores** — Breaks automation if trusted without calibration
6. **Docker memory errors with GGUF models** — Deployment failures; test containerized deployment early

**Recommended prevention focus:**
- **Phase 1:** Model selection (German support, adequate context window), negation handling in prompts, evidence grounding in schema
- **Phase 2:** Validation on real GGPONC/BRONCO data, confidence calibration, entity normalization
- **Phase 3:** Docker memory configuration, proper health checks, end-to-end testing with production-like constraints

**High-risk areas requiring deeper research:**
- German compound word handling across different model tokenizers
- Hallucination detection/prevention strategies for extraction tasks
- Confidence score calibration methods for German medical LLMs

**Low-risk areas (standard patterns available):**
- FastAPI endpoint implementation
- Pydantic schema validation
- JSON parsing and error handling
