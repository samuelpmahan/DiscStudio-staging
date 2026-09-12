/** Public entry points for the three deliberately small PxC algorithm references. */
import { createLab } from '../lab/lab.js';
import { registerDecisionTree, runDecisionTree } from './decision-tree.js';
import { registerPerceptron, runPerceptron } from './perceptron.js';
import { registerTransformer, runTransformer } from './transformer.js';

export { runDecisionTree, runPerceptron, runTransformer };
export * from './decision-tree.js';
export * from './perceptron.js';
export * from './transformer.js';

/** A convenience LAB with all reference Calculations registered once. */
export function createReferenceLab() {
  const lab = createLab();
  registerDecisionTree(lab);
  registerPerceptron(lab);
  registerTransformer(lab);
  return lab;
}
export { createLiveReference, createLiveTransport, projectReferenceFrame, REFERENCE_FIELDS } from './live.js';
