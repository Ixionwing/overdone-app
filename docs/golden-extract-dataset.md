# Overdone — Golden Extraction Dataset (Starter Evals)

This dataset contains real-world, unpolished user phrasing across 10 core input categories to evaluate and benchmark the `Pydantic AI` extraction engine for the **Overdone** diagnostic webapp.

---

## 1. Relative Load (`add` / relative deltas)

1. `"add 20 lb to bench tomorrow"`  
   * **Extracted**: `scope: session` | `action: relative (+20 lb)` | `exercise: Bench Press` | `timeframe: tomorrow`
2. `"bumping my squat up by 15 pounds next leg day"`  
   * **Extracted**: `scope: session` | `action: relative (+15 lb)` | `exercise: Squat` | `timeframe: next leg day`
3. `"throw an extra 5kg on overhead press"`  
   * **Extracted**: `scope: session` | `action: relative (+5 kg)` | `exercise: Overhead Press` | `timeframe: next session`
4. `"i want to add 2 sets of pullups to my back workout friday"`  
   * **Extracted**: `scope: session` | `action: relative (+2 sets)` | `exercise: Pull-up` | `timeframe: Friday`
5. `"gonna try adding 10lbs on incline db bench"`  
   * **Extracted**: `scope: session` | `action: relative (+10 lb)` | `exercise: Incline Dumbbell Bench Press` | `timeframe: unspecified session`
6. `"drop 10 lbs off deadlift tomorrow"`  
   * **Extracted**: `scope: session` | `action: relative (-10 lb)` | `exercise: Deadlift` | `timeframe: tomorrow`
7. `"tack on 5 lbs to weighted dips for my next chest session"`  
   * **Extracted**: `scope: session` | `action: relative (+5 lb)` | `exercise: Weighted Dip` | `timeframe: next chest session`
8. `"increase lateral raises by 2.5kg next push workout"`  
   * **Extracted**: `scope: session` | `action: relative (+2.5 kg)` | `exercise: Lateral Raise` | `timeframe: next push workout`
9. `"add 1 set of calf raises at the end of leg day"`  
   * **Extracted**: `scope: session` | `action: relative (+1 set)` | `exercise: Calf Raise` | `timeframe: next leg day`
10. `"wanna add 25 pounds to my leg press on tuesday"`  
    * **Extracted**: `scope: session` | `action: relative (+25 lb)` | `exercise: Leg Press` | `timeframe: Tuesday`
11. `"can i add 5 lbs to DB shoulder press today?"`  
    * **Extracted**: `scope: session` | `action: relative (+5 lb)` | `exercise: Dumbbell Shoulder Press` | `timeframe: today`
12. `"bumping up barbell rows by 10kg"`  
    * **Extracted**: `scope: session` | `action: relative (+10 kg)` | `exercise: Barbell Row` | `timeframe: unspecified session`

---

## 2. Absolute Load (target absolute weight)

1. `"bring pushdown up to 40 lb"`  
   * **Extracted**: `scope: session` | `action: absolute (40 lb)` | `exercise: Tricep Pushdown` | `timeframe: next session`
2. `"i want to bench 225 tomorrow"`  
   * **Extracted**: `scope: session` | `action: absolute (225 lb)` | `exercise: Bench Press` | `timeframe: tomorrow`
3. `"squatting 315 on my next lower body day"`  
   * **Extracted**: `scope: session` | `action: absolute (315 lb)` | `exercise: Squat` | `timeframe: next lower body day`
4. `"taking deadlift to 180kg for friday's heavy pull session"`  
   * **Extracted**: `scope: session` | `action: absolute (180 kg)` | `exercise: Deadlift` | `timeframe: Friday`
5. `"want my overhead press at 135 lbs today"`  
   * **Extracted**: `scope: session` | `action: absolute (135 lb)` | `exercise: Overhead Press` | `timeframe: today`
6. `"set leg extension stack to 150 lbs for 3 sets"`  
   * **Extracted**: `scope: session` | `action: absolute (150 lb, 3 sets)` | `exercise: Leg Extension` | `timeframe: next session`
7. `"gonna work up to 80lb dumbbells on chest press"`  
   * **Extracted**: `scope: session` | `action: absolute (80 lb DBs)` | `exercise: Dumbbell Chest Press` | `timeframe: next session`
8. `"bring cable rows to 60kg next time"`  
   * **Extracted**: `scope: session` | `action: absolute (60 kg)` | `exercise: Cable Row` | `timeframe: next time`
9. `"hit 100 lbs on hip thrusts tomorrow"`  
   * **Extracted**: `scope: session` | `action: absolute (100 lb)` | `exercise: Hip Thrust` | `timeframe: tomorrow`
10. `"aiming for 50kg barbell curl on arms day"`  
    * **Extracted**: `scope: session` | `action: absolute (50 kg)` | `exercise: Barbell Curl` | `timeframe: arms day`
11. `"moving my lat pulldown to 140 lbs next workout"`  
    * **Extracted**: `scope: session` | `action: absolute (140 lb)` | `exercise: Lat Pulldown` | `timeframe: next workout`
12. `"target 90 lb DBs on flat bench next week"`  
    * **Extracted**: `scope: session` | `action: absolute (90 lb DBs)` | `exercise: Flat Dumbbell Bench Press` | `timeframe: next week`

---

## 3. Full Prescription (`sets x reps @ weight`)

1. `"3 sets of 8 @ 40lb on tricep pushdowns"`  
   * **Extracted**: `scope: session` | `exercise: Tricep Pushdown` | `prescription: 3 sets x 8 reps @ 40 lb`
2. `"do 4x5 @ 275lbs squat tomorrow"`  
   * **Extracted**: `scope: session` | `exercise: Squat` | `prescription: 4 sets x 5 reps @ 275 lb` | `timeframe: tomorrow`
3. `"5x5 bench press at 100kg next monday"`  
   * **Extracted**: `scope: session` | `exercise: Bench Press` | `prescription: 5 sets x 5 reps @ 100 kg` | `timeframe: next Monday`
4. `"3x10 leg press 400 lbs on leg day"`  
   * **Extracted**: `scope: session` | `exercise: Leg Press` | `prescription: 3 sets x 10 reps @ 400 lb` | `timeframe: next leg day`
5. `"want to hit 1 set of 3 @ 405lb deadlift RPE 9"`  
   * **Extracted**: `scope: session` | `exercise: Deadlift` | `prescription: 1 set x 3 reps @ 405 lb (RPE 9)`
6. `"4 sets of 12 reps with 35lb dumbbells for incline flyes"`  
   * **Extracted**: `scope: session` | `exercise: Incline Dumbbell Fly` | `prescription: 4 sets x 12 reps @ 35 lb DBs`
7. `"3x15 @ 50kg lat pulldown today"`  
   * **Extracted**: `scope: session` | `exercise: Lat Pulldown` | `prescription: 3 sets x 15 reps @ 50 kg` | `timeframe: today`
8. `"doing 5x3 at 145 lbs overhead press friday"`  
   * **Extracted**: `scope: session` | `exercise: Overhead Press` | `prescription: 5 sets x 3 reps @ 145 lb` | `timeframe: Friday`
9. `"2x8 @ 90lb db bench press then 1xAMRAP"`  
   * **Extracted**: `scope: session` | `exercise: Dumbbell Bench Press` | `prescription: 2 sets x 8 reps @ 90 lb + 1 set AMRAP @ 90 lb`
10. `"3 sets 10 reps seated cable row at 120 pounds"`  
    * **Extracted**: `scope: session` | `exercise: Seated Cable Row` | `prescription: 3 sets x 10 reps @ 120 lb`
11. `"4x8 Bulgarian split squats @ 40lb dumbbells"`  
    * **Extracted**: `scope: session` | `exercise: Bulgarian Split Squat` | `prescription: 4 sets x 8 reps @ 40 lb DBs`
12. `"3x12 hamstring curls @ 110lbs on lower day"`  
    * **Extracted**: `scope: session` | `exercise: Hamstring Curl` | `prescription: 3 sets x 12 reps @ 110 lb`

---

## 4. Time Horizon / Macro Goals

1. `"i want to bench 225 by next month"`  
   * **Extracted**: `scope: macro_goal` | `timeframe: 1 month (4 weeks)` | `target: absolute (225 lb)` | `exercise: Bench Press`
2. `"reach a 405 squat over the next 8 weeks"`  
   * **Extracted**: `scope: macro_goal` | `timeframe: 8 weeks` | `target: absolute (405 lb)` | `exercise: Squat`
3. `"add 30 lbs to my deadlift in 6 weeks"`  
   * **Extracted**: `scope: macro_goal` | `timeframe: 6 weeks` | `target: relative (+30 lb)` | `exercise: Deadlift`
4. `"want to be able to overhead press 185 by end of the year"`  
   * **Extracted**: `scope: macro_goal` | `timeframe: ~3-4 months` | `target: absolute (185 lb)` | `exercise: Overhead Press`
5. `"increase weekly pullup volume by 20% over the next month"`  
   * **Extracted**: `scope: macro_goal` | `timeframe: 4 weeks` | `target: relative volume (+20%)` | `exercise: Pull-up`
6. `"hit 100kg bench press within 6 weeks"`  
   * **Extracted**: `scope: macro_goal` | `timeframe: 6 weeks` | `target: absolute (100 kg)` | `exercise: Bench Press`
7. `"work up to 50lb db incline press by christmas"`  
   * **Extracted**: `scope: macro_goal` | `timeframe: ~3 months` | `target: absolute (50 lb DBs)` | `exercise: Incline Dumbbell Press`
8. `"get my squat from 275 to 315 in 30 days"`  
   * **Extracted**: `scope: macro_goal` | `timeframe: 30 days (4 weeks)` | `target: progression (275 -> 315 lb)` | `exercise: Squat`
9. `"build up to 4 sets of 10 dips with +45lbs over 2 months"`  
   * **Extracted**: `scope: macro_goal` | `timeframe: 2 months (8 weeks)` | `target: prescription (4x10 @ +45 lb)` | `exercise: Dip`
10. `"double my leg press tonnage in 6 weeks"`  
    * **Extracted**: `scope: macro_goal` | `timeframe: 6 weeks` | `target: relative volume (2x tonnage)` | `exercise: Leg Press`
11. `"gain 15lbs on my barbell row baseline over the next 4 weeks"`  
    * **Extracted**: `scope: macro_goal` | `timeframe: 4 weeks` | `target: relative (+15 lb)` | `exercise: Barbell Row`
12. `"reach 500lb deadlift club by summer"`  
    * **Extracted**: `scope: macro_goal` | `timeframe: ~5 months` | `target: absolute (500 lb)` | `exercise: Deadlift`

---

## 5. Multi-Lift Session Prompts

1. `"+10 bench, +5 incline, +3 sets pushdowns tomorrow"`  
   * **Extracted**: `scope: session (multi-lift)` | `items: [Bench Press (+10 lb), Incline Bench Press (+5 lb), Tricep Pushdown (+3 sets)]`
2. `"add 15 lbs to squat, 10 lbs to RDL, and 2 sets of leg curls"`  
   * **Extracted**: `scope: session (multi-lift)` | `items: [Squat (+15 lb), Romanian Deadlift (+10 lb), Leg Curl (+2 sets)]`
3. `"tomorrow: 225x5 bench, 80x8 db incline, and 50lb cable flyes"`  
   * **Extracted**: `scope: session (multi-lift)` | `items: [Bench Press (225 lb x 5), Incline DB Bench (80 lb x 8), Cable Fly (50 lb)]`
4. `"bumping up deadlift by 20 lbs and overhead press by 5 lbs on friday"`  
   * **Extracted**: `scope: session (multi-lift)` | `items: [Deadlift (+20 lb), Overhead Press (+5 lb)]`
5. `"add 1 set to pullups, +5kg on barbell row, and +10lbs on lat pulldown"`  
   * **Extracted**: `scope: session (multi-lift)` | `items: [Pull-up (+1 set), Barbell Row (+5 kg), Lat Pulldown (+10 lb)]`
6. `"increase leg press to 450, add 10 lbs to calf raises, +1 set leg extensions"`  
   * **Extracted**: `scope: session (multi-lift)` | `items: [Leg Press (450 lb), Calf Raise (+10 lb), Leg Extension (+1 set)]`
7. `"+5 lbs db curls, +10 lbs hammer curls, +2 sets tricep extensions for arms"`  
   * **Extracted**: `scope: session (multi-lift)` | `items: [Dumbbell Curl (+5 lb), Hammer Curl (+10 lb), Tricep Extension (+2 sets)]`
8. `"wanna do 315 squat, 225 bench, and 405 deadlift in one session"`  
   * **Extracted**: `scope: session (multi-lift)` | `items: [Squat (315 lb), Bench Press (225 lb), Deadlift (405 lb)]`
9. `"add 10lb to overhead press and subtract 5lb from lateral raises"`  
   * **Extracted**: `scope: session (multi-lift)` | `items: [Overhead Press (+10 lb), Lateral Raise (-5 lb)]`
10. `"bumping bench press by 5kg and adding 2 sets of dips tomorrow"`  
    * **Extracted**: `scope: session (multi-lift)` | `items: [Bench Press (+5 kg), Dip (+2 sets)]`
11. `"+10 lbs on front squat, +15 lbs on hip thrust, and 1 extra set of split squats"`  
    * **Extracted**: `scope: session (multi-lift)` | `items: [Front Squat (+10 lb), Hip Thrust (+15 lb), Split Squat (+1 set)]`
12. `"take lat pulldown to 150lb, facepulls to 60lb, and add 2 sets of shrugs"`  
    * **Extracted**: `scope: session (multi-lift)` | `items: [Lat Pulldown (150 lb), Face Pull (60 lb), Barbell Shrug (+2 sets)]`

---

## 6. Exercise Nicknames & Shorthand

1. `"add 10 lbs to DB bench"`  
   * **Extracted**: `nickname: DB bench` -> `canonical: Dumbbell Bench Press` | `action: relative (+10 lb)`
2. `"bring OHP to 135 tomorrow"`  
   * **Extracted**: `nickname: OHP` -> `canonical: Overhead Press` | `action: absolute (135 lb)`
3. `"add 20 lbs on RDLs for leg day"`  
   * **Extracted**: `nickname: RDLs` -> `canonical: Romanian Deadlift` | `action: relative (+20 lb)`
4. `"+15 lbs to BB row"`  
   * **Extracted**: `nickname: BB row` -> `canonical: Barbell Row` | `action: relative (+15 lb)`
5. `"3 sets of 10 on rear delts"`  
   * **Extracted**: `nickname: rear delts` -> `canonical: Rear Delt Fly / Reverse Fly` | `prescription: 3x10`
6. `"add 10kg on conventional"`  
   * **Extracted**: `nickname: conventional` -> `canonical: Conventional Deadlift` | `action: relative (+10 kg)`
7. `"take skullcrushers up to 70 lbs"`  
   * **Extracted**: `nickname: skullcrushers` -> `canonical: Lying Triceps Extension (Skullcrusher)` | `action: absolute (70 lb)`
8. `"do 4 sets of 12 on preacher curls"`  
   * **Extracted**: `nickname: preacher curls` -> `canonical: Preacher Curl` | `prescription: 4x12`
9. `"bump up sissy squats by 10 lbs"`  
   * **Extracted**: `nickname: sissy squats` -> `canonical: Sissy Squat` | `action: relative (+10 lb)`
10. `"+5 lbs on incline DBs"`  
    * **Extracted**: `nickname: incline DBs` -> `canonical: Incline Dumbbell Bench Press` | `action: relative (+5 lb)`
11. `"add 2 sets to hammy curls"`  
    * **Extracted**: `nickname: hammy curls` -> `canonical: Hamstring / Leg Curl` | `action: relative (+2 sets)`
12. `"bring incline barbell up to 185"`  
    * **Extracted**: `nickname: incline barbell` -> `canonical: Incline Barbell Bench Press` | `action: absolute (185 lb)`
13. `"add 10 lbs on pec deck tomorrow"`  
    * **Extracted**: `nickname: pec deck` -> `canonical: Butterfly / Pec Deck Fly` | `action: relative (+10 lb)`

---

## 7. Fatigue / Sleep Clauses Direct in Prompt

1. `"only slept 4 hours and feel beat up, but I want to add 10 lbs to bench tomorrow"`  
   * **Extracted**: `scope: session` | `exercise: Bench Press (+10 lb)` | `fatigue_flag: "only slept 4 hours and feel beat up"`
2. `"feeling super sore from tuesday, but wanna try adding 5kg to squat today"`  
   * **Extracted**: `scope: session` | `exercise: Squat (+5 kg)` | `fatigue_flag: "feeling super sore from tuesday"`
3. `"exhausted from work and low energy, aiming for 225 bench anyway"`  
   * **Extracted**: `scope: session` | `exercise: Bench Press (225 lb)` | `fatigue_flag: "exhausted from work and low energy"`
4. `"slept terrible last night, can i still add 15 lbs to deadlift?"`  
   * **Extracted**: `scope: session` | `exercise: Deadlift (+15 lb)` | `fatigue_flag: "slept terrible last night"`
5. `"lower back is stiff today, wanting to do 315 squat"`  
   * **Extracted**: `scope: session` | `exercise: Squat (315 lb)` | `fatigue_flag: "lower back is stiff today"`
6. `"feeling under the weather, adding 5lbs to overhead press"`  
   * **Extracted**: `scope: session` | `exercise: Overhead Press (+5 lb)` | `fatigue_flag: "feeling under the weather"`
7. `"shoulder feels a bit twingey, but wanna bump incline db bench to 70s"`  
   * **Extracted**: `scope: session` | `exercise: Incline DB Bench (70 lb DBs)` | `fatigue_flag: "shoulder feels a bit twingey"`
8. `"drained from CNS fatigue from yesterday's heavy pull, adding 2 sets of squats tomorrow"`  
   * **Extracted**: `scope: session` | `exercise: Squat (+2 sets)` | `fatigue_flag: "drained from CNS fatigue"`
9. `"fasted today and energy is low, bring pushdowns up to 50 lbs"`  
   * **Extracted**: `scope: session` | `exercise: Tricep Pushdown (50 lb)` | `fatigue_flag: "fasted today and energy is low"`
10. `"working on 3 hours of sleep, add 20 lbs to leg press"`  
    * **Extracted**: `scope: session` | `exercise: Leg Press (+20 lb)` | `fatigue_flag: "working on 3 hours of sleep"`
11. `"elbow aching slightly, wanna add 5 lbs to barbell curl"`  
    * **Extracted**: `scope: session` | `exercise: Barbell Curl (+5 lb)` | `fatigue_flag: "elbow aching slightly"`
12. `"knee feels cranky, but planning 4x8 @ 245lb squat"`  
    * **Extracted**: `scope: session` | `exercise: Squat (4x8 @ 245 lb)` | `fatigue_flag: "knee feels cranky"`

---

## 8. "Or tell me what to do instead" (Substitution Requests)

1. `"i want to add 30 lbs to my bench press tomorrow, or tell me what to do instead"`  
   * **Extracted**: `scope: session` | `exercise: Bench Press (+30 lb)` | `substitution_requested: true`
2. `"add 20 lbs to overhead press, but if that's overdoing it what exercise should i swap to?"`  
   * **Extracted**: `scope: session` | `exercise: Overhead Press (+20 lb)` | `substitution_requested: true`
3. `"bring squat to 365, or give me a safer alternative lower body move"`  
   * **Extracted**: `scope: session` | `exercise: Squat (365 lb)` | `substitution_requested: true`
4. `"+15 lbs on barbell rows tomorrow, or suggest a safer back exercise if too high"`  
   * **Extracted**: `scope: session` | `exercise: Barbell Row (+15 lb)` | `substitution_requested: true`
5. `"add 3 extra heavy sets of dips, or tell me a better chest finisher"`  
   * **Extracted**: `scope: session` | `exercise: Dip (+3 heavy sets)` | `substitution_requested: true`
6. `"jump deadlift by 40 lbs friday, or what should i do instead?"`  
   * **Extracted**: `scope: session` | `exercise: Deadlift (+40 lb)` | `substitution_requested: true`
7. `"add 10kg to incline db press, or offer a safer substitute"`  
   * **Extracted**: `scope: session` | `exercise: Incline DB Bench (+10 kg)` | `substitution_requested: true`
8. `"take leg press to 500 lbs tomorrow, or advise a safer set/rep scheme"`  
   * **Extracted**: `scope: session` | `exercise: Leg Press (500 lb)` | `substitution_requested: true`
9. `"+10 lbs on skullcrushers, or suggest another tricep exercise if my elbows will complain"`  
   * **Extracted**: `scope: session` | `exercise: Skullcrusher (+10 lb)` | `substitution_requested: true`
10. `"aiming for 225 bench press next week, or recommend a better progression plan"`  
    * **Extracted**: `scope: session/macro` | `exercise: Bench Press (225 lb)` | `substitution_requested: true`
11. `"add 25 lbs on RDLs tomorrow or recommend a safer posterior chain exercise"`  
    * **Extracted**: `scope: session` | `exercise: Romanian Deadlift (+25 lb)` | `substitution_requested: true`
12. `"bring shoulder press to 80lb DBs or tell me what to swap it with"`  
    * **Extracted**: `scope: session` | `exercise: Dumbbell Shoulder Press (80 lb DBs)` | `substitution_requested: true`

---

## 9. Amount with No Unit (Implicit Unit Check)

1. `"add 20 to bench tomorrow"`  
   * **Extracted**: `scope: session` | `exercise: Bench Press` | `raw_value: 20` | `unit_specified: false`
2. `"bring pushdown up to 40"`  
   * **Extracted**: `scope: session` | `exercise: Tricep Pushdown` | `raw_value: 40` | `unit_specified: false`
3. `"take squat to 315 next leg day"`  
   * **Extracted**: `scope: session` | `exercise: Squat` | `raw_value: 315` | `unit_specified: false`
4. `"bumping overhead press by 10 on friday"`  
   * **Extracted**: `scope: session` | `exercise: Overhead Press` | `raw_value: 10` | `unit_specified: false`
5. `"want to hit 225 for 5 reps on bench"`  
   * **Extracted**: `scope: session` | `exercise: Bench Press` | `raw_value: 225 (5 reps)` | `unit_specified: false`
6. `"add 5 to lateral raises"`  
   * **Extracted**: `scope: session` | `exercise: Lateral Raise` | `raw_value: 5` | `unit_specified: false`
7. `"take deadlift to 405 next week"`  
   * **Extracted**: `scope: session` | `exercise: Deadlift` | `raw_value: 405` | `unit_specified: false`
8. `"bumping barbell rows up by 15"`  
   * **Extracted**: `scope: session` | `exercise: Barbell Row` | `raw_value: 15` | `unit_specified: false`
9. `"3 sets of 8 @ 50 on cable rows"`  
   * **Extracted**: `scope: session` | `exercise: Cable Row` | `prescription: 3x8 @ raw_value: 50` | `unit_specified: false`
10. `"add 25 to leg press on tuesday"`  
    * **Extracted**: `scope: session` | `exercise: Leg Press` | `raw_value: 25` | `unit_specified: false`
11. `"bring db bench up to 80s"`  
    * **Extracted**: `scope: session` | `exercise: Dumbbell Bench Press` | `raw_value: 80 (DB pairs)` | `unit_specified: false`
12. `"increase lat pulldown by 10 tomorrow"`  
    * **Extracted**: `scope: session` | `exercise: Lat Pulldown` | `raw_value: 10` | `unit_specified: false`

---

## 10. Anything that feels "unfair" if `extract_failed` (Edge Cases)

1. `"bench 2 plates tomorrow"`  
   * **Extracted**: `scope: session` | `exercise: Bench Press` | `action: absolute (225 lb / 100 kg equivalent)`  
   * *Challenge*: Slang term `"2 plates"` = 225 lb (or 100 kg).
2. `"add a quarter to each side of my squat"`  
   * **Extracted**: `scope: session` | `exercise: Squat` | `action: relative (+50 lb total / +25 lb per side)`  
   * *Challenge*: Slang term `"quarter"` = 25 lb weight plate per side.
3. `"wanna throw a dime on my bench press"`  
   * **Extracted**: `scope: session` | `exercise: Bench Press` | `action: relative (+20 lb total / +10 lb per side)`  
   * *Challenge*: Slang term `"dime"` = 10 lb weight plate per side.
4. `"gonna max out on deadlift friday, aiming for 4 plates"`  
   * **Extracted**: `scope: session` | `exercise: Deadlift` | `action: absolute (405 lb / 180 kg equivalent)`  
   * *Challenge*: Slang term `"4 plates"` = 405 lb.
5. `"add 10lbs to DB incline bench press, 5lbs on lateral raises and do 3 sets of 12 pushdowns @ 40lbs"`  
   * **Extracted**: `scope: session (multi-lift)` | `items: [Incline DB Bench (+10 lb), Lat Raise (+5 lb), Pushdown (3x12 @ 40 lb)]`  
   * *Challenge*: Dense multi-part sentence mixing relative deltas and full prescriptions.
6. `"can i add 15 lbs to my bench press or is that too much?"`  
   * **Extracted**: `scope: session` | `exercise: Bench Press` | `action: relative (+15 lb)`  
   * *Challenge*: Conversational question format wrapped in hesitation.
7. `"im thinking of adding 10 lbs to my bench but my shoulder has been kinda iffy since last week"`  
   * **Extracted**: `scope: session` | `exercise: Bench Press` | `action: relative (+10 lb)` | `fatigue_flag: "shoulder has been kinda iffy"`  
   * *Challenge*: Run-on sentence blending target intent with historical symptom narrative.
8. `"jump from 185 to 205 on incline barbell in 2 weeks"`  
   * **Extracted**: `scope: macro_goal` | `exercise: Incline Barbell Bench Press` | `progression: 185 -> 205 lb over 2 weeks`  
   * *Challenge*: Explicit state-transition declaration (`A -> B`).
9. `"wanna do 5x5 bench @ 80% 1RM tomorrow"`  
   * **Extracted**: `scope: session` | `exercise: Bench Press` | `prescription: 5x5 @ 80% 1RM`  
   * *Challenge*: Percentage-of-1RM intensity notation.
10. `"bumping up tricep pushdowns by two notches on the cable stack"`  
    * **Extracted**: `scope: session` | `exercise: Tricep Pushdown` | `action: relative (+2 pin increments / notches)`  
    * *Challenge*: Non-weight equipment metric (`notches`/`pins`).
11. `"add 5kg to bench and do 4x10 @ 60kg squat next leg day"`  
    * **Extracted**: `scope: session (multi-lift)` | `items: [Bench Press (+5 kg), Squat (4x10 @ 60 kg)]`  
    * *Challenge*: Mixed relative delta and full prescription across different body parts.
12. `"bring my bench up 10 pounds each week for the next month"`  
    * **Extracted**: `scope: macro_goal` | `exercise: Bench Press` | `rate: +10 lb/week for 4 weeks (+40 lb total)`  
    * *Challenge*: Velocity-based rate increment across time horizon.
13. `"add 10 lbs to bench tomorrow (current 185lb)"`  
    * **Extracted**: `scope: session` | `exercise: Bench Press` | `action: relative (+10 lb)` | `user_stated_baseline: 185 lb`  
    * *Challenge*: In-prompt inline baseline declaration in parentheses.
