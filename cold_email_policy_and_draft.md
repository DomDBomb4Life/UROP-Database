# Cold Email Policy for MIT LLM UROP Outreach

## The Policy (for future LLM agent use)

### Who to email (per professor)

Each outreach batch is organized around **one professor (PI)** and all the lab groups / UROP projects they sponsor. For each batch, generate the following and **send them all at the same time**:

1. **One separate email for each grad student** whose work overlaps with the UROP topic(s). These emails can be similar to each other — the grad students won't see each other's emails. Each email should reference that specific grad student's work and the project track most relevant to them. Do NOT CC the professor on these.
2. **One master email to the professor directly.** This email covers the full scope of the lab's UROP offerings, briefly notes which project tracks interest you and why, and is more concise than the grad student emails. It's okay to email the professor even for small labs — they're the ones who ultimately approve UROPs.

**Follow-up protocol:** If a grad student doesn't respond in ~10 days, follow up once (2 sentences). If still no response, try a different grad student in the same lab with a fresh email. The professor email gets one follow-up at Day 10 and that's it.

### What to include

- **Subject line**: Short, specific, not generic. Reference the project name or a specific technical hook. Never "UROP Inquiry" by itself. **Every outreach email must include the tag `--UROP--` somewhere in the subject line** — this enables Apple Smart Mailbox filtering to collect all UROP outreach in one view. Place it at the end of the subject so it reads naturally, e.g. "Agent Benchmarking UROP — summer availability --UROP--".
- **Opening line**: One sentence that establishes why you're emailing *them specifically*. Not a thesis statement about your life.
- **The "connection" paragraph**: If you have a warm lead (shared advisor, took their class, read a specific paper), put it here. If you read a paper, mention ONE specific thing about the methodology or result — not a summary of the abstract. This is where you prove you actually looked at their work.
- **The "what I bring" paragraph**: 2-3 sentences max. What you've actually done (be honest and specific), not what you're "passionate about." Undersell rather than oversell. If your research experience was grunt work, say you ran experiments and learned the tools — don't claim you led a research direction.
- **The ask**: Be direct. Are you asking about summer availability? Fall positions? Say exactly what you want and when.
- **Sign-off**: Short. Attach nothing. Say you can send a resume if they're interested.

### What to avoid

- **Resume dumps**: Don't list your accomplishments. The email is about THEIR work and why you want to contribute to it. Your resume comes later.
- **"Passionate about AI" language**: Dead giveaway of a mass email. Replace passion with specifics.
- **Summarizing their paper back to them**: They wrote it, they know what it says. Instead, mention what about it caught your attention or what question it raised for you.
- **Overselling**: If you fine-tuned Llama models as a research assistant, say that. Don't say you "developed novel alignment methods."
- **Multiple questions**: One ask per email. Don't ask about the project AND whether they're hiring AND what courses you should take.
- **"I am a freshman at MIT" as the opening line**: Lead with the work, not your year. If your year is a liability (e.g., the listing says Juniors/Seniors), address it honestly but briefly — after you've already shown you're competent.

### Timing and follow-ups

- Send Tuesday–Thursday, 9am–11am EST.
- **All emails in a batch (professor + all grad students) go out at the same time.** Do not stagger them.
- If no response in 10 days, follow up once. Keep it to 2 sentences.
- If still no response from a grad student, email a different grad student in the lab with a fresh email (not a forward).
- The professor gets one follow-up at Day 10. That's it.

---

## Stress Test: Raskar Lab — "LLM Agent Benchmarking & Multi-Modal Data Selection"

### Lab Intel

**Lab**: Camera Culture Group, MIT Media Lab
**PI**: Ramesh Raskar (raskar@mit.edu) — Associate Professor, directs Camera Culture and NANDA (Networked Agents and Decentralized AI)
**UROP Contact**: Charles Lu (luchar@mit.edu) — PhD student, NSF fellow, data-centric ML, published at NeurIPS/ICML/AAAI

**Current grad students in the group:**

| Name | Email | Research Focus |
|------|-------|----------------|
| Charles Lu | luchar@mit.edu | Data-centric ML, LLM source attribution, data markets (NeurIPS 2024) |
| Siddharth Somasundaram | (via Media Lab) | Computational imaging |
| Kushagra Tiwary | (via Media Lab) | Computational imaging |
| Nikhil Behari | (via Media Lab) | (check group page) |
| Aaron Young | (via Media Lab) | (check group page) |

**Note on prior experience**: Your current LLM fine-tuning work gives you direct technical relevance to both tracks. Lead with the skills (LoRA, quantization, evaluation pipelines), not the lab lineage.

**Key observation about this UROP**: The listing says "Juniors and Seniors" under eligible years. You're a freshman. This needs to be addressed, but AFTER you demonstrate competence. The fact that you already have LLM fine-tuning experience and are working in a lab that came out of this group is your strongest argument.

**Two tracks offered:**
1. Agent Benchmarking — building adaptive AI interviewer systems that grade agents on task completion
2. Multi-Modal Data Valuation — scalable data selection for LLM/RLHF post-training, quantifying value of image-text data points

**Charles Lu's relevant papers to reference:**
- "Data Acquisition via Experimental Design for Data Markets" (NeurIPS 2024) — his most recent first-author work, directly relevant to the data valuation track
- "Conformal Prediction with Large Language Models for Multi-Choice QA" (ICML 2023 Workshop) — directly ties to LLM evaluation

**Raskar's relevant project:**
- NANDA: building an "Internet of AI Agents" — foundational infrastructure for networked AI agents, extending protocols like MCP

### Email #1a: To Raskar (master professor email)

**To**: raskar@mit.edu
**Subject**: Camera Culture UROP — interest in agent benchmarking & data valuation tracks --UROP--

Hi Professor Raskar,

I'm a first-year Course 6-4 student reaching out about the LLM Agent Benchmarking & Multi-Modal Data Selection UROP. Both tracks are compelling — the agent benchmarking side because static leaderboards don't capture multi-step tool use, and the data valuation side because quantifying marginal contribution of multimodal data seems like an increasingly important problem as post-training data pipelines scale.

I've spent this year doing LLM fine-tuning work — LoRA-based adaptation of Llama models, evaluation pipelines, quantization — so I have a working knowledge of the stack these projects build on. I realize the posting lists Juniors and Seniors; I wanted to ask whether there's any flexibility, and whether summer involvement is a possibility. Happy to send my resume if helpful.

Thanks for your time,
Dominik Bach
MIT '29 — AI & Decision Making
mit_bach@mit.edu

---

### Email #1b: To Charles Lu (grad student email)

**To**: luchar@mit.edu
**Subject**: LLM Agent Benchmarking UROP — question about summer availability --UROP--

Hi Charles,

I saw the LLM Agent Benchmarking & Multi-Modal Data Selection listing on ELX and wanted to reach out. I'm particularly interested in the agent benchmarking track — the idea of moving past static leaderboards toward adaptive evaluation feels like the right problem to be working on, especially as agents start handling multi-step tool use where a single accuracy number doesn't tell you much.

I've been reading your NeurIPS 2024 paper on data acquisition via experimental design, and the framework for quantifying data value seems like it would connect well with the data valuation track too. One thing I've been curious about is how those valuation methods scale when the data is multimodal — whether image-text pairs behave differently from text-only in terms of marginal contribution.

Quick background on me: I'm a first-year Course 6-4 student. I've spent this year doing LLM fine-tuning work — mostly running LoRA-based adaptation of Llama models for client-specific tasks on short cycles. It's been hands-on work with PyTorch, quantization, and evaluation pipelines rather than anything I'd call novel research, but it's given me a solid working knowledge of the fine-tuning stack.

I realize the posting lists Juniors and Seniors. I wanted to ask honestly whether there's any flexibility there, and also whether there's any possibility of getting involved over the summer — either remotely or on campus. I'd be happy to send along my resume if it's helpful.

Thanks for your time,
Dominik Bach
MIT '29 — AI & Decision Making
mit_bach@mit.edu

---

### Why this email works (annotation for policy)

**Subject line**: Names the specific project + states the actual question (summer) + includes the `--UROP--` key tag for Smart Mailbox filtering. Not generic.

**Opening**: Goes straight to the project. Mentions a specific technical opinion about WHY adaptive evaluation matters (multi-step tool use). This isn't flattery — it's showing he understands the problem space.

**Paper reference**: Doesn't summarize the paper. Instead, raises a genuine question (how does data valuation scale for multimodal data?) that shows he read it and thought about it. This is the kind of thing that makes a grad student think "this person would be useful in lab meeting."

**Experience paragraph**: Honest. "Mostly running LoRA-based adaptation" and "hands-on work... rather than anything I'd call novel research." This is exactly right — it shows self-awareness and avoids the trap of overselling a grunt role. Mentions specific tools (PyTorch, quantization, evaluation pipelines) without listing them like a resume. Does NOT name-drop prior advisors or try to justify a connection to the lab beyond the skills themselves.

**The freshman problem**: Addressed directly ("I realize the posting lists Juniors and Seniors") but only AFTER demonstrating competence. The ask is honest: "is there flexibility?" Not "I know I'm only a freshman but..."

**The summer ask**: Clear, specific, one question. Doesn't bundle in five other requests.

**No resume attached**: Offers to send it if asked. This keeps the email from feeling like a mass application.

**Batch structure**: The grad student email and professor email go out simultaneously. The professor email is shorter and covers the full lab scope. The grad student email is more detailed and references their specific work. Neither CCs the other — this avoids the awkward dynamic of the professor seeing a grad-student-targeted email.

---

### If Charles doesn't respond: Follow-up (Day 10)

**To**: luchar@mit.edu
**Subject**: Re: LLM Agent Benchmarking UROP — question about summer availability --UROP--

Hi Charles — just bumping this in case it got buried. Happy to work around whatever timeline works for the group. Thanks again.

Dominik

---

### If still no response: Email to Nikhil Behari or Aaron Young (Day 20)

This would be a fresh email (NOT a forward) to another grad student in Camera Culture, asking more generally about UROP opportunities in the group rather than the specific listing. The structure stays the same — lead with their work, be honest about your level, drop the Vepakomma connection.

---

## Key Adjustments for Other Labs

This policy should be adapted per-lab:

- **For labs with no ELX listing** (e.g., Omar Khattab's new lab): The email becomes a cold inquiry rather than a response to a posting. Lead with their recent paper, ask if they're taking UROPs. These emails should be shorter (~150 words).
- **For labs where the professor IS the contact** (e.g., Manolis Kellis's listings go to kellis-admin): Email the admin address, but the email content should still reference specific work by a grad student or postdoc if possible.
- **For fall-only listings**: Ask about summer remote work explicitly. Frame it as wanting to ramp up before the fall so you can hit the ground running.
- **For multimodal/robotics labs** (e.g., Torralba, Bobu): Lean on your LLM experience as complementary to their vision/robotics work, not as a direct match. "I've been working on the language model side and want to understand how these models interface with [vision/embodied systems]."