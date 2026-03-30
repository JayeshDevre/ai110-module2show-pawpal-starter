from pawpal_system import Task, Pet, Owner, Scheduler

# --- 1. Create two pets ---
mochi = Pet(name="Mochi", species="dog")
luna = Pet(name="Luna", species="cat")

# --- 2. Add tasks to Mochi (dog) ---
mochi.add_task(Task("Morning walk",    duration_minutes=20, priority="high",   category="walk"))
mochi.add_task(Task("Breakfast",       duration_minutes=10, priority="high",   category="feed"))
mochi.add_task(Task("Flea medication", duration_minutes=5,  priority="high",   category="meds",  frequency="weekly"))
mochi.add_task(Task("Brushing",        duration_minutes=15, priority="medium", category="groom"))
mochi.add_task(Task("Backyard playtime", duration_minutes=30, priority="low",  category="enrichment"))

# --- 3. Add tasks to Luna (cat) ---
luna.add_task(Task("Feeding",          duration_minutes=5,  priority="high",   category="feed"))
luna.add_task(Task("Litter box clean", duration_minutes=10, priority="medium", category="groom"))
luna.add_task(Task("Interactive play", duration_minutes=15, priority="low",    category="enrichment"))

# --- 4. Create owner with a 90-minute daily time budget ---
jordan = Owner(name="Jordan", available_minutes=90)
jordan.add_pet(mochi)
jordan.add_pet(luna)

# --- 5. Run the scheduler and print the plan ---
scheduler = Scheduler(owner=jordan)
scheduler.build_schedule()

print("=" * 50)
print("        PAWPAL+ — TODAY'S SCHEDULE")
print("=" * 50)
print(scheduler.summary())
print("=" * 50)
