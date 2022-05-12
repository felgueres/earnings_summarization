## Earnings Call Summarization 

### Background

Earnings calls are quarterly events where management first presents the company's business outlook and it’s followed by probing questions from an audience of investment analysts.

Earnings Calls are a key source of information to understand a company’s state of affairs and thus, investor decision-making. The fact that it’s real-time, prevents window dressing statements and a higher signal-to-noise ratio relative to investor reports.

### Problem Statement

Reading through a 5-10 page earnings call transcript takes an investor 30mins to 1hr of his time. A casual investor doesn’t have the time nor is it reasonable to go through any >10 stock portfolio, so they recur to summaries provided by media outlets like news and finance apps. These media outlets usually have 2-3 analysts summarize the earnings call transcripts. 

There’s clear value in the summary (ie. saved time for investors) and significant labor that goes into producing these summaries (ie. conservatively, 3 hrs @ 50 USD/hr, ~150USD/summary).

Supposing it’s possible to generate human quality summaries with AI, the cost of producing an Earnings Call summary will be ~10X lower.

### Goals
- Train a transformer model with Earnings Call transcripts and summaries that produces human-quality summaries.

- Generate summaries for all Space & Defense primes (5), Automotive Manufacturers (3), Chip Manufacturers (3), and Space SPACs. 

- Build a UI to present Earnings Call summaries.


