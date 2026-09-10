# Task 47

Intent: neat never reuses an id: next_id also counts the landing receipts (task-N, undo-task-N, failed), so an undone or killed task's number is not handed out again; selftest proves it
Starting point: cb5736cfe509c9005ffefed75147ad1ff352bce1 (land(task-40): parallel you can see: the Tick viewer draws a Tick's Calculations side by side when they are parallel branches, prints the Tick's work and latency and the run's critical path, shows placement when the record carries it, and tick_laws names Ticks; the students record is the demo page)
Verify: bash pyto/scripts/neat.sh selftest
Allow: pyto/scripts/neat.sh pyto/LANDING.md pyto/experiments/tasks
Candidate: not packed yet
Evidence: not packed yet

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)
