# Task 103

Intent: brain/backend six more primitives and the case table learns which engines answer: matrix_rank, pinv, correlate, diff, gradient and outer, each with its oracle Part per engine and benchmark Parts at three sizes; and the py engine of matrix_rank refuses the band its own svd cannot resolve - taking square roots of the eigenvalues of a-transpose-a squares the condition number, so a truly zero singular value comes back near sqrt of eps and numpy's rank tolerance sits far below anything that engine can see - which is why a case may now name the engines that answer it instead of being deleted from the table
Starting point: daad2bf5dc3d87920640b20d188bfe6599b28c97 (land(task-102): brain ml multiclass: softmax (multinomial) logistic regression beside the one-vs-rest one, and gradient boosting for classification on the logistic loss with its second-order step, each fit and predict a separate Calculation over a json-able model Part, oracled against scipy minimising the same cross-entropy and against the probabilities the fit itself recorded)
Verify: cd pyto && python -m unittest discover -s experiments/brain -p 'test_*.py'
Allow: pyto/experiments/brain pyto/experiments/tasks
Candidate: not packed yet
Evidence: not packed yet

## Uncertain

{?} both runs are in the packet: the copy's venv (python 3.11, numpy 2.4.6) through the Verify
line, and python 3.12.3 with numpy 2.5.3 and scipy 1.18.1 at
experiments/tasks/103/evidence/verify-python312-numpy253.txt. 728 tests, OK in both.
{?} a case may now carry `engines=("np", "sp")`. It is not a way to excuse a disagreement - every
engine a case names must still match the reference - it is how a case one engine refuses BY DESIGN
stays in the table instead of being quietly deleted from it. Two cases use it today
(matrix_rank/deficient_6x4 and pinv/deficient_6x4) and the map says why.
{?} the py engine of matrix_rank refuses a band rather than answering in it: between numpy's rank
tolerance (max(m,n) * eps * sigma_max) and its own svd's error floor (about sqrt(eps) * sigma_max),
a singular value is genuinely ambiguous to an engine that went through a^T a. The floor constant is
sqrt of the float64 epsilon, written as a literal; a one-sided jacobi svd would remove the whole
question and is in the map's next list.
{?} the py engine of pinv is r^-1 q^T from the reduced qr, so it is a left inverse of a
full-column-rank matrix and nothing else. It refuses the rest by name; np and sp answer.
{?} correlate's sp engine is pinned to scipy.signal.correlate(method="direct") so all three engines
do the same arithmetic; an fft-based correlate is a different backend with a different tolerance.
