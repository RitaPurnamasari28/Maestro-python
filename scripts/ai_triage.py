# Ai will analize the failed tests and generate a triage report
import os
import json
import glob
from openai import OpenAI


def triage_failures(allure_results_dir="allure-results"):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("No API Key. Skipping AI Triage.")
        return
    # currectly ai_triage will not created if no key detected

    client = OpenAI(
        api_key=api_key, base_url=os.getenv("AI_BASE_URL", "https://api.openai.com/v1")
    )
    failed_tests = []

    for file in glob.glob(f"{allure_results_dir}/*-result.json"):
        with open(file, "r") as f:
            data = json.load(f)
            if data.get("status") in ["failed", "broken"]:
                failed_tests.append(
                    {
                        "name": data.get("name"),
                        "trace": data.get("statusDetails", {}).get(
                            "trace", "No trace available"
                        ),
                    }
                )

    if not failed_tests:
        print("No failures to triage.")
        return

    report_content = "# AI Failure Triage Report\n\n"
    system_prompt = "You are an expert QA Automation Engineer diagnosing test failures. Analyze the provided error trace strictly in this order: 1. Exception or failed assertion? 2. Locator resolved? 3. Preconditions met? 4. Expected value correct? 5. Flaky? Verdict options: [Script/Environment Defect], [Product Bug], [Flaky]. Provide verdict and 2-3 sentences evidence. DO NOT auto-close or rewrite logic."

    for test in failed_tests:
        try:
            response = client.chat.completions.create(
                model=os.getenv("AI_MODEL", "gpt-4o"),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": f"Test Name: {test['name']}\nTrace:\n{test['trace']}",
                    },
                ],
            )
            analysis = response.choices[0].message.content
            report_content += f"## Test: {test['name']}\n{analysis}\n\n---\n"
        except Exception as e:
            report_content += (
                f"## Test: {test['name']}\nFailed to generate AI triage: {e}\n\n---\n"
            )

    with open("triage_report.md", "w") as f:
        f.write(report_content)
    print("Triage report generated: triage_report.md")


if __name__ == "__main__":
    triage_failures()
