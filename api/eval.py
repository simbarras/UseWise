# ruff: noqa: ANN001, ANN201, FBT002, TRY003, EM101, EM102, E501

import argparse
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

try:
    from dotenv import load_dotenv as _load_dotenv
except ImportError:  # pragma: no cover
    _load_dotenv = None


URL = "https://openrouter.ai/api/v1"
SUF = "_privacy_policy"
FLASH = [
    ["This policy says your data is shared with other companies.", "flag"],
    ["This policy says cookies or similar tracking tools are used.", "flag"],
    ["This policy says you can ask for your data to be deleted.", "flag"],
    ["This policy says you can access or correct your data.", "flag"],
    ["This policy says your data may be used for ads or marketing.", "flag"],
    ["This policy says your data may be transferred to other countries.", "flag"],
    ["How long does the company keep your personal data?", "time"],
]
FOLLOW = [
    "What personal information do you collect about me?",
    "Why do you collect my data?",
    "Who do you share my data with?",
    "Do you sell my data or use it for advertising?",
    "How long do you keep my data?",
    "What happens to my data if I delete my account?",
    "Can I ask to see the data you have about me?",
    "Can I ask you to correct wrong information about me?",
    "Can I download a copy of my data?",
    "How can I opt out of tracking or marketing?",
    "Is my data sent or stored outside my country?",
    "Do you collect sensitive data or data about children?",
]

CONSUMER_FLASH_QUESTIONS = tuple((q, k) for q, k in FLASH)
CONSUMER_FOLLOW_UP_QUESTIONS = tuple(FOLLOW)


def sys_msg(pp):
    return SystemMessage(
        content=(
            "You are a helpful assistant that answers questions on the "
            f"following privacy policy:\n\n{pp}"
        )
    )


def flash_msg(yn, tq):
    yn = "\n".join(f"{i+1}. {q}" for i, q in enumerate(yn))
    tq = "\n".join(f"{i+1}. {q}" for i, q in enumerate(tq))
    return f"""
Analyze the privacy policy provided in the system message.

Your task is to extract structured information.

1) For each of the following yes/no statements:
   - Answer with true or false.
   - Use true only if the policy clearly confirms the statement.
   - If the policy does not mention it or is unclear, answer false.
   - Keep the same order.

YES/NO STATEMENTS:
{yn}

2) For each of the following time-related questions:
   - Extract the duration mentioned in the policy.
   - Return a short human-readable phrase
     (e.g., "1 year", "6 months", "30 days",
     "Until account deletion", "Indefinitely").
   - Keep the same order.

TIME QUESTIONS:
{tq}

3) Based on your analysis, provide an overall privacy risk score
   from 1 (very low risk) to 10 (very high risk).

Return only JSON with this exact shape:
{{"flags": [true, false], "times": ["1 year"], "score": 5}}
"""


def follow_msg(q):
    return (
        f"{q}\n\nAnswer in at most two short sentences. "
        "Be direct, consumer-friendly, and only use the policy."
    )


def get_consumer_flash_questions():
    return [tuple(x) for x in FLASH]


def get_consumer_follow_up_questions():
    return list(FOLLOW)


def load_env():
    if _load_dotenv:
        _load_dotenv()


def load_openrouter_api_key():
    load_env()
    return os.environ["OPENROUTER_API_KEY"]


def resolve_models(cli, env_models=None):
    if cli:
        return cli
    if env_models:
        return [x.strip() for x in env_models.split(",") if x.strip()]
    return []


def headers():
    h = {}
    if os.getenv("OPENROUTER_HTTP_REFERER"):
        h["HTTP-Referer"] = os.environ["OPENROUTER_HTTP_REFERER"]
    if os.getenv("OPENROUTER_APP_TITLE"):
        h["X-Title"] = os.environ["OPENROUTER_APP_TITLE"]
    return h


def name(path):
    s = path.stem
    return s.removesuffix(SUF)


def discover_policy_paths(dir_, selected_policies=None, include_sample=False):
    ps = sorted(Path(dir_).glob("*.txt"))
    if not selected_policies:
        return [p for p in ps if p.stem.endswith(SUF) or include_sample]
    lut = {k: p for p in ps for k in [p.name, p.stem, name(p)]}
    out = [lut[p] for p in selected_policies if p in lut]
    miss = sorted(p for p in selected_policies if p not in lut)
    if miss:
        msg = f"Unknown policies: {', '.join(miss)}"
        raise ValueError(msg)
    return out


def load_policies(paths):
    return {name(p): p.read_text(encoding="utf-8") for p in paths}


def client(model, cfg, key):
    base = os.getenv("OPENROUTER_BASE_URL", URL)
    hdrs = headers()
    if cfg["max_tokens"] is None:
        return ChatOpenAI(
            model=model,
            base_url=base,
            api_key=key,
            temperature=cfg["temperature"],
            timeout=cfg["timeout"],
            default_headers=hdrs,
        )
    return ChatOpenAI(
        model=model,
        base_url=base,
        api_key=key,
        temperature=cfg["temperature"],
        timeout=cfg["timeout"],
        default_headers=hdrs,
        model_kwargs={"max_tokens": cfg["max_tokens"]},
    )


def split_qs(qs):
    return [q for q, k in qs if k == "flag"], [q for q, k in qs if k == "time"]


def flash_run(llm, pp, qs=None):
    qs = qs or get_consumer_flash_questions()
    yn, tq = split_qs(qs)
    msgs = [sys_msg(pp), HumanMessage(content=flash_msg(yn, tq))]
    raw = str(llm.invoke(msgs).content).strip()
    raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    data = json.loads(raw)
    fs = iter(data.get("flags", []))
    ts = iter(data.get("times", []))
    ans = []
    for q, k in qs:
        ans.append({"question": q, "type": k, "value": next(fs) if k == "flag" else next(ts)})
    return {"answers": ans, "score": data["score"]}


def follow_run(llm, pp, qs=None):
    qs = qs or get_consumer_follow_up_questions()
    sm = sys_msg(pp)
    return [
        {"question": q, "answer": str(llm.invoke([sm, HumanMessage(content=follow_msg(q))]).content)}
        for q in qs
    ]


def tick(i, n, label=""):
    w = 28
    f = 0 if not n else int(w * i / n)
    bar = f"{'#' * f}{'.' * (w - f)}"
    end = "\n" if i >= n else ""
    sys.stderr.write(f"\r{label} [{bar}] {i}/{n}" + end)
    sys.stderr.flush()


def run_one(llm, pol, pp, cfg):
    row = {}
    row["policy"] = pol
    row["flash_latency_seconds"] = None
    row["flash_score"] = None
    row["flash_answers"] = []
    row["flash_error"] = None
    row["follow_up_latency_seconds"] = None
    row["follow_up_answers"] = []
    row["follow_up_error"] = None
    t = perf_counter()
    try:
        out = flash_run(llm, pp)
        row["flash_score"] = out["score"]
        row["flash_answers"] = out["answers"]
    except Exception as e:  # noqa: BLE001
        row["flash_error"] = f"{type(e).__name__}: {e}"
    row["flash_latency_seconds"] = perf_counter() - t
    if not cfg["follow_up"]:
        return row
    t = perf_counter()
    try:
        row["follow_up_answers"] = follow_run(llm, pp)
    except Exception as e:  # noqa: BLE001
        row["follow_up_error"] = f"{type(e).__name__}: {e}"
    row["follow_up_latency_seconds"] = perf_counter() - t
    return row


def evaluate(models, policies, cfg, key):
    total = len(models) * len(policies) * (2 if cfg["follow_up"] else 1)
    done = 0
    res = []
    for m in models:
        llm = client(m, cfg, key)
        item = {"model": m, "policies": []}
        for pol, pp in policies.items():
            row = run_one(llm, pol, pp, cfg)
            item["policies"].append(row)
            done += 1
            tick(done, total, m)
            if cfg["follow_up"]:
                done += 1
                tick(done, total, m)
        res.append(item)
    return res


def avg(xs):
    return round(sum(xs) / len(xs), 2) if xs else None


def print_report(results, follow_up=False):
    print("\nOpenRouter privacy policy eval")  # noqa: T201
    print("=" * 31)  # noqa: T201
    for mr in results:
        lats = [p["flash_latency_seconds"] for p in mr["policies"] if p["flash_latency_seconds"] is not None]
        ok = sum(1 for p in mr["policies"] if not p["flash_error"])
        fok = sum(1 for p in mr["policies"] if p["follow_up_answers"] and not p["follow_up_error"])
        print(f"\nModel: {mr['model']}")  # noqa: T201
        print(f"  Flash summary success: {ok}/{len(mr['policies'])}")  # noqa: T201
        if avg(lats) is not None:
            print(f"  Avg flash latency: {avg(lats):.2f}s")  # noqa: T201
        if follow_up:
            print(f"  Follow-up success: {fok}/{len(mr['policies'])}")  # noqa: T201
        for p in mr["policies"]:
            print(f"  - Policy: {p['policy']}")  # noqa: T201
            if p["flash_error"]:
                print(f"    Flash error: {p['flash_error']}")  # noqa: T201
            else:
                print(f"    Risk score: {p['flash_score']}/10")  # noqa: T201
                for a in p["flash_answers"]:
                    print(f"    Flash - {a['question']} => {a['value']}")  # noqa: T201
            if follow_up:
                msg = p["follow_up_error"] or f"{len(p['follow_up_answers'])} questions"
                pre = "Follow-up error: " if p["follow_up_error"] else "Follow-up responses: "
                print(f"    {pre}{msg}")  # noqa: T201


def payload(models, names, cfg, results):
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "provider": "openrouter",
        "models": models,
        "policies": names,
        "include_follow_up": cfg["follow_up"],
        "temperature": cfg["temperature"],
        "timeout": cfg["timeout"],
        "max_tokens": cfg["max_tokens"],
        "flash_questions": [q for q, _ in FLASH],
        "follow_up_questions": FOLLOW if cfg["follow_up"] else [],
        "results": results,
    }


def parser():
    p = argparse.ArgumentParser(description="Evaluate OpenRouter models on privacy policy summaries.")
    p.add_argument("--models", nargs="+", help="OpenRouter model IDs. Falls back to OPENROUTER_MODELS if omitted.")
    p.add_argument("--policies", nargs="*", help="Policy names, stems, or filenames from test_data.")
    p.add_argument("--include-sample", action="store_true", help="Include sample .txt files that are not named *_privacy_policy.txt.")
    p.add_argument("--follow-up", action="store_true", help="Also run the 12 consumer follow-up questions for each model.")
    p.add_argument("--output", type=Path, help="Optional path for a JSON results file.")
    p.add_argument("--temperature", type=float, default=float(os.getenv("EVAL_TEMPERATURE", "0")), help="Sampling temperature. Defaults to EVAL_TEMPERATURE or 0.")
    p.add_argument("--timeout", type=float, default=None, help="Optional request timeout in seconds.")
    p.add_argument("--max-tokens", type=int, default=None, help="Optional max tokens for each response.")
    return p


def main():
    args = parser().parse_args()
    models = resolve_models(args.models, os.getenv("OPENROUTER_MODELS"))
    if not models:
        raise SystemExit("Provide --models or set OPENROUTER_MODELS.")
    try:
        key = load_openrouter_api_key()
    except KeyError as e:
        raise SystemExit(f"Missing required environment variable: {e.args[0]}") from e
    cfg = {
        "follow_up": args.follow_up,
        "temperature": args.temperature,
        "timeout": args.timeout,
        "max_tokens": args.max_tokens,
    }
    root = Path(__file__).resolve().parent / "test_data"
    try:
        paths = discover_policy_paths(root, args.policies, args.include_sample)
    except ValueError as e:
        raise SystemExit(str(e)) from e
    if not paths:
        raise SystemExit(f"No .txt policies found in {root}")
    pols = load_policies(paths)
    res = evaluate(models, pols, cfg, key)
    print_report(res, args.follow_up)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(payload(models, list(pols), cfg, res), indent=2), encoding="utf-8")
        print(f"\nSaved results to {args.output}")  # noqa: T201


if __name__ == "__main__":
    main()
