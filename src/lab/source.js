/** Where the LAB's own documents are kept, copied byte for byte from ChainSpot b5a6ae0. */
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
export const SOURCE = join(dirname(fileURLToPath(import.meta.url)), 'source');
