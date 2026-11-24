# Project Documentation

Customer Support AI is the formal project name. The assistant is **Averse — the Customer Support AI**.

- [Day 2 Knowledge-Base Audit and Completion Report](DAY_2_COMPLETION_REPORT.md)
- [Knowledge-Base README](KNOWLEDGE_BASE_README.md)
- [Supervisor Review Items and Evidence Gaps](SUPERVISOR_REVIEW_ITEMS.md)
- [Day 3 Dataset Specification](DAY_3_DATASET_SPECIFICATION.md)
- [Day 3 Readiness Report](DAY_3_READINESS_REPORT.md)
- [Day 3 Dataset Completion Report](DAY_3_DATASET_COMPLETION_REPORT.md)
- [Day 4 Phase 1 Completion Report](DAY_4_PHASE_1_COMPLETION_REPORT.md)
- [Day 4 Phase 2 Classifier Evaluation](DAY_4_PHASE_2_CLASSIFIER_EVALUATION.md)
- [Day 4 Closure Report](DAY_4_CLOSURE_REPORT.md)

The Day 4 validation evaluation identifies Naive Bayes as the leading experimental candidate (51/56 correct) and the current softmax model as unsuitable for routing (it predicted `out_of_scope` for all 56 records). Both model artifacts remain preserved under `data/models/day4-text-processing-v2/` and `data/day3-v1.1.0/` respectively. Neither classifier is production-ready. The project answers only from approved public Bank of Zambia passages. Dataset validation does not verify factual accuracy or runtime referral behavior.
