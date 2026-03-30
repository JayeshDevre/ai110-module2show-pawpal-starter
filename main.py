from pawpal_system import Task, Pet, Owner, Scheduler

# --- Setup ---
mochi = Pet(name="Mochi", species="dog")
luna  = Pet(name="Luna",  species="cat")

mochi.add_task(Task("Morning walk",    duration_minutes=20, priority="high",   category="walk"))
mochi.add_task(Task("Breakfast",       duration_minutes=10, priority="high",   category="feed"))
mochi.add_task(Task("Brushing",        duration_minutes=15, priority="medium", category="groom"))
luna.add_task( Task("Feeding",         duration_minutes=5,  priority="high",   category="feed"))
luna.add_task( Task("Litter box clean",duration_minutes=10, priority="medium", category="groom"))

jordan = Owner(name="Jordan", available_minutes=90)
jordan.add_pet(mochi)
jordan.add_pet(luna)

# ── 1. Normal schedule (no conflicts) ────────────────────────────────────────
print("=" * 55)
print("  NORMAL SCHEDULE — no conflicts expected")
print("=" * 55)
scheduler = Scheduler(owner=jordan)
scheduler.build_schedule()
print(scheduler.summary())

# ── 2. Force two tasks at the same time to trigger conflict detection ─────────
print("\n" + "=" * 55)
print("  CONFLICT DEMO — two tasks manually placed at 8:00 AM")
print("=" * 55)

# Create a fresh scheduler and build the normal schedule first
scheduler2 = Scheduler(owner=jordan)
scheduler2.build_schedule()

# Manually inject a task that starts at 8:00 AM (offset=480) — same start as the
# first scheduled task — using force_add() to bypass the greedy algorithm.
# This simulates a scenario where an external event or manual override causes overlap.
clash_task = Task("Vet call", duration_minutes=15, priority="high", category="meds")
scheduler2.force_add(clash_task, start_offset=8 * 60)   # 8:00 AM = 480 min

# detect_conflicts() checks every pair with overlaps_with() and returns warning strings.
# It never raises — just returns an empty list if the schedule is clean.
conflicts = scheduler2.detect_conflicts()

if conflicts:
    print("  Conflict detected in schedule:")
    for w in conflicts:
        print(w)
else:
    print("  No conflicts found.")

print()
print("  Full schedule with conflict report:")
print(scheduler2.summary())
