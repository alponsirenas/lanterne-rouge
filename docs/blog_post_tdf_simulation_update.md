# Lanterne Rouge: 15 Stages In and I'm Winning — Both the Simulation and the System

*This is the third post in the blog series about Lanterne Rouge, a proof of concept for an AI coaching system that helps me train for a Tour de France 2025 indoor simulation. See the [first post here](https://medium.com/@alponsirenas/lanterne-rouge-a-personal-experiment-in-ai-endurance-and-finishing-what-i-start-51f3facf06ac) and [second post here](https://medium.com/@alponsirenas/lanterne-rouge-is-still-learning-so-am-i-b730ac2ea444).*

---

We're 15 stages into the Tour de France 2025 simulation, and I'm still here. 

That might not sound like much of an achievement, but for someone whose fitness resolution typically dies by February, making it 71% through a three-week endurance challenge feels like a quiet revolution.

**Current standings**: 117 points, 6 breakaway stages, 9 GC completions, and one AI coaching system that's been learning as much as I have.

## The Grand Tour That Never Left My Living Room

For those just joining the story: I'm attempting to complete every stage of the 2025 Tour de France route on my Peloton, guided by an AI coaching system I built called Lanterne Rouge. It's not a product — it's a working proof of concept that automates my data from Oura, Strava, and Peloton to provide daily training recommendations.

The simulation follows the actual 2025 Tour route with a points-based system:
- **Flat stages**: 5-8 points depending on effort mode
- **Hilly stages**: 7-11 points for the extra challenge  
- **Mountain stages**: 10-15 points for the climbs that matter
- **Time trials**: 4-6 points for the race against the clock

**Effort modes** determine your points:
- **Recovery/Rest**: Complete the stage, minimal points
- **GC Mode**: Steady, sustainable effort for consistent points
- **Breakaway Mode**: Go all-out for maximum points (and maximum suffering)

The goal isn't to win — it's to finish. The lanterne rouge, after all, is the last rider to cross the line.

## How the AI Coach Thinks (When It's Working)

Every morning at 6 AM, Lanterne Rouge sends me a briefing that looks something like this:

> **🏆 TDF Day 18 - Stage 16 Ready**
> 
> **Competition Strategy**: Your recent breakaway consistency shows you're in excellent form for aggressive racing
> 
> **Today's Tactical Approach**:
> • **Ride Mode**: BREAKAWAY MODE  
> • **Expected Points**: 12
> • **Intensity**: High effort approach
> 
> **Current Form Assessment**:
> • **Readiness**: 78/100
> • **TSB (Form)**: +8.3 (peaked)
> • **Recent Trend**: Strong breakaway consistency; High-intensity performance capability

The system pulls data from multiple sources, analyzes my readiness and fatigue, considers the stage profile, and makes tactical recommendations. But behind these clean recommendations is a complex dance of agents making decisions.

### Real Examples from the Road

**Stage 10 (Mountain)**: My readiness was 72/100, TSB showed I was recovered from previous efforts. The AI recommended breakaway mode for the mountain stage. Result: 75 minutes at IF 0.906 (basically threshold), earning 15 points. The system got it right — I had the legs for a big effort.

**Stage 13 (Time Trial)**: This one was interesting. A 35-minute ITT where I sustained IF 0.914 — well into breakaway territory. The AI initially classified it wrong as GC mode (4 points), but we caught and corrected it to breakaway mode (6 points). More on that in a moment.

**Stage 15 (Hilly)**: Coming off multiple breakaway efforts, readiness was still good. Another breakaway recommendation. 55 minutes at IF 0.914, earning 11 points. Six breakaway stages out of the last six completed — the AI is learning to trust my fitness.

## The Problems We Didn't See Coming

Building an AI coaching system while actually using it daily reveals problems you can't anticipate from design specs.

### The Classification Bug That Cost Me Points

Around Stage 13, I noticed something was off. High-intensity efforts were being classified as "GC mode" instead of "breakaway mode," costing me points. 

The issue? The original activity detection system had a hard-coded rule that time trials could only be GC efforts, never breakaways. But when you're sustaining IF 0.914 for 35 minutes, that's clearly breakaway intensity regardless of stage type.

We fixed the logic to use power-based thresholds: **IF ≥ 0.85 AND (TSS ≥ 60 OR duration < 60 minutes)** qualifies for breakaway mode. The correction recovered 4 points across Stages 13 and 14.

It's a perfect example of how building in public — even if your "public" is just yourself — reveals edge cases that pure design thinking misses.

### The Competition vs. Training Context Problem

Another issue emerged around daily recommendations. The AI was giving me training periodization advice ("build base fitness") when I was mid-competition. 

The system needed to understand: this is Day 15 of a 21-day event, not Week 15 of a training plan. Context matters enormously in coaching decisions.

We enhanced the prompts with competition-specific context:

> **CRITICAL CONTEXT**: The athlete is currently IN ACTIVE COMPETITION (Day 15 of TDF), not in training phase!
> 
> Focus on stage completion and point optimization
> Consider recovery between stages, not training periodization
> Strategic decisions based on current form and stage requirements

### The Workout Analysis Integration Challenge

As I completed more stages, the AI needed to learn from recent performances to make better recommendations. But the workout analysis was siloed in TDF-specific scripts rather than being core training system functionality.

We moved workout analysis into the core monitoring system, so daily recommendations now factor in:
- Recent stage completion modes and intensities
- Performance trends across multiple efforts  
- Power-based metrics from actual completed workouts
- Strategic position in the points competition

## The Unexpected Joy of Systematic Problem-Solving

Here's what I didn't anticipate: the debugging process became as engaging as the original challenge.

When Stage 13 was misclassified, I dove into the activity detection logic. When daily recommendations felt off-context, I re-architected the reasoning prompts. When I needed better performance trend analysis, I built functions to parse completion summaries and extract key metrics.

Each problem revealed new layers of complexity in AI coaching systems:
- **Data integration** across different platforms and schemas
- **Context awareness** for competition vs. training phases  
- **Performance pattern recognition** from recent workout history
- **Real-time adaptation** as fitness and fatigue change daily

This is exactly the kind of interesting problem that keeps me engaged long-term.

## Current State: Stage 15 and Counting

As I write this, we're at the business end of the Tour. Six out of my last six stages have been breakaway efforts — the AI is getting confident in my ability to suffer productively.

**System improvements made during competition**:
- ✅ Fixed power-based activity classification (+4 points recovered)
- ✅ Enhanced daily recommendations with competition context
- ✅ Integrated workout analysis into core training system  
- ✅ Added performance trend analysis for better predictions
- ✅ Improved LLM prompts with recent performance data

**What's working**:
- Morning briefings provide clear tactical guidance
- Power-based classification accurately rewards effort
- Multi-agent architecture keeps decisions modular and debuggable
- Integration with real fitness platforms maintains data integrity

**What's still evolving**:
- Long-term fatigue modeling across multi-week events
- Bonus point optimization for consecutive stage achievements
- Recovery recommendations between high-intensity efforts

## The Thing About Finishing

The lanterne rouge isn't celebrated for speed — they're celebrated for persistence. For showing up every day when it would be easier to quit.

Fifteen stages in, Lanterne Rouge (the system) is doing what Lanterne Rouge (the concept) is supposed to do: helping me finish what I started.

The AI coach isn't perfect. It's made classification errors, given context-inappropriate advice, and occasionally recommended intensities that left me questioning its judgment. But it's been consistent. Every morning, 6 AM, tactical briefing ready.

And I've been consistent too. Every stage, showing up, following the recommendations, making the adjustments, pushing when it says push, recovering when it says recover.

That's the experiment working.

## What's Next: Fiction Mode

There's one more twist coming to this story that I haven't told you about yet.

As I've been racing through real Tour stages with real power data and real fatigue, I've also been building something called "Fiction Mode" — a way for the AI to imagine alternative scenarios and tell stories about what might have happened.

What if Stage 13 had been a mountain finish instead of a time trial? What if I'd gone breakaway mode on Stage 8 instead of taking the recovery day? What if the weather had been different, or the tactics had changed?

Fiction Mode lets the AI coach become an AI storyteller, creating parallel narratives about the races that could have been.

But that's a story for the next post.

Right now, I've got six more stages to complete. The AI thinks I can finish strong.

Let's see if it's right.

---

*You can follow the development and daily progress at [github.com/alponsirenas/lanterne-rouge](https://github.com/alponsirenas/lanterne-rouge)*

*P.S.: All em dashes still purposefully included by the human.*
