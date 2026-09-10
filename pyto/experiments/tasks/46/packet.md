# Task 46

Intent: the suite is green on three OSes and two Python versions: the grouped-ablation suite fails on CI under Python 3.12 (ubuntu and windows) and the students grader fails on windows; find the cause from the CI logs and a local Python 3.10 run, fix it in the tests or the scripts without regenerating evidence, and make check_all.yml upload the per-suite logs as the receipt
Starting point: 0f9f6d32e8213e9dee91f7ef54b6cc9ef6603b6c (land(task-45): KT answers: five questions from the local session (what moved registry to OS and what is unproved; which corrections overturned the most and where the old assumptions survive; glue that holds real methods; what a successor would follow and miss; when a question advanced the project) answered from the record at pyto/research/kt-answers.md)
Verify: python3 -c "import yaml; yaml.safe_load(open('.github/workflows/check_all.yml'))" && cd pyto && python3 -m unittest discover -s experiments/grouped-ablation -p 'test_*.py' && cd experiments/students && python3 -m unittest discover -s . -p 'test_*.py'
Allow: pyto/experiments/grouped-ablation/replay.py pyto/experiments/grouped-ablation/retain.py pyto/experiments/grouped-ablation/test_replay.py pyto/experiments/grouped-ablation/test_retain.py pyto/experiments/grouped-ablation/test_materials.py pyto/experiments/grouped-ablation/test_run_cached.py pyto/experiments/grouped-ablation/run_cached.py pyto/experiments/grouped-ablation/materials.py pyto/experiments/students/grade.py pyto/experiments/students/homework.py pyto/experiments/students/test_students.py pyto/scripts/check_all.sh .github/workflows/check_all.yml pyto/CHANGES.md pyto/experiments/tasks
Candidate: not packed yet
Evidence: not packed yet

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)
