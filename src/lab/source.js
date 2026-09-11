/** Where the LAB's own documents are kept, copied byte for byte from ChainSpot b5a6ae0. */
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
export const SOURCE = join(dirname(fileURLToPath(import.meta.url)), 'source');

/**
 * Where the Stages this port invents are kept. S0..S3 were read out of the LAB
 * and their documents are copies; S4, S5 and S6 have no ChainSpot original, so
 * their `.mmd` sources live here rather than under `source/`, and the ported
 * compiler turns each into the same document the Stage's own `s<N>Document`
 * builds (structural digest equal), which is the check the LAB applies to S0/S1.
 */
export const STAGES = join(dirname(fileURLToPath(import.meta.url)), 'stages');
