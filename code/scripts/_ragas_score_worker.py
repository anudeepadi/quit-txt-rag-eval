#!/usr/bin/env python3
"""Subprocess worker: score one RAGAS metric in an isolated interpreter.

ragas 0.4.3's embeddings-backed metrics wedge their async connection pool
on Python 3.13 (frozen CPU, idle sockets) when scored in a long-lived
process. Running each metric in its own interpreter makes the OS the
cleanup mechanism and lets the parent enforce a hard timeout.

stdin:  JSON {"metric": str, "model": str, "inputs": [dict, ...]}
stdout: JSON list of scores (null where scoring failed)
stderr: progress lines (inherited by the parent's log)
"""

import asyncio
import json
import os
import sys

# Must be set before any ragas import: ragas's usage telemetry does blocking
# network I/O inside the event loop, and an unreachable analytics endpoint
# stalls scoring indefinitely (verified: the embeddings-backed metrics hung
# until this was disabled).
os.environ.setdefault("RAGAS_DO_NOT_TRACK", "true")

from openai import AsyncOpenAI
from ragas.embeddings import OpenAIEmbeddings as RagasOpenAIEmbeddings
from ragas.llms import llm_factory
from ragas.metrics.collections import (
    AnswerRelevancy,
    ContextPrecision,
    ContextRecall,
    Faithfulness,
)

_CHUNK_SIZE = 10


def _build_metric(name: str, model: str):
    client = AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])
    llm = llm_factory(model, provider="openai", client=client, max_tokens=8192)
    if name == "faithfulness":
        return Faithfulness(llm=llm)
    if name == "answer_relevancy":
        return AnswerRelevancy(llm=llm, embeddings=RagasOpenAIEmbeddings(client=client))
    if name == "context_precision":
        return ContextPrecision(llm=llm)
    if name == "context_recall":
        return ContextRecall(llm=llm)
    raise ValueError(f"unknown metric: {name}")


async def _main() -> None:
    payload = json.load(sys.stdin)
    name, model, inputs = payload["metric"], payload["model"], payload["inputs"]
    scores: list = []
    for start in range(0, len(inputs), _CHUNK_SIZE):
        chunk = inputs[start:start + _CHUNK_SIZE]
        try:
            results = await _build_metric(name, model).abatch_score(chunk)
            scores.extend(
                float(r.value) if r is not None and r.value is not None else None
                for r in results
            )
        except Exception as e:
            print(f"      [worker WARN] {name} at sample {start}: {e}",
                  file=sys.stderr, flush=True)
            scores.extend([None] * len(chunk))
        print(f"      [{min(start + _CHUNK_SIZE, len(inputs))}/{len(inputs)}] scored",
              file=sys.stderr, flush=True)
        await asyncio.sleep(2)
    json.dump(scores, sys.stdout)


if __name__ == "__main__":
    asyncio.run(_main())
