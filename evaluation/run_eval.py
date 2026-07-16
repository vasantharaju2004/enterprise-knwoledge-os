from reasoning.chains.rag_chain import answer_question
from evaluation.golden_set import GOLDEN_SET


def run_evaluation():
    results = []

    for case in GOLDEN_SET:
        response = answer_question(
            question=case["question"],
            document_id=case["document_id"],
        )
        answer_text = response["answer"].lower()

        match_mode = case.get("match_mode", "all")

        found = [kw for kw in case["expected_keywords"] if kw.lower() in answer_text]
        if match_mode == "any":
            passed = len(found) > 0
        else:
            missing = [
                kw for kw in case["expected_keywords"] if kw.lower() not in answer_text
            ]
            passed = len(missing) == 0

        results.append(
            {
                "question": case["question"],
                "passed": passed,
                "found": found,
                "missing": missing,
                "answer": response["answer"],
            }
        )

    total = len(results)
    passed_count = sum(1 for r in results if r["passed"])

    print(f"\n{'=' * 60}")
    print(f"EVALUATION RESULTS: {passed_count}/{total} passed")
    print(f"{'=' * 60}\n")

    for r in results:
        status = "PASS" if r["passed"] else "FAIL"
        print(f"[{status}] {r['question']}")
        if not r["passed"]:
            print(f"       Missing: {r['missing']}")
            print(f"       Got: {r['answer'][:150]}")
        print()

    return results


if __name__ == "__main__":
    run_evaluation()
