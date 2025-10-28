# backend/IA/resume.py
from transformers import pipeline

summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

def summarize_text_local(text: str, max_length: int = 150, min_length: int = 50) -> str:
    sentences = text.split(". ")
    segments = []
    current_segment = ""

    for s in sentences:
        if len(current_segment.split()) + len(s.split()) <= 200:
            current_segment += s + ". "
        else:
            segments.append(current_segment.strip())
            current_segment = s + ". "
    if current_segment:
        segments.append(current_segment.strip())

    summaries = []
    for seg in segments:
        summary_list = summarizer(seg, max_length=max_length, min_length=min_length, do_sample=False)
        summaries.append(summary_list[0]['summary_text'])

    return " ".join(summaries)
