import fs from 'node:fs';
import path from 'node:path';
import {main} from './evaluate.mjs';
// Expand supplied directories deterministically; explicit files retain argument order.
const paths=process.argv.slice(2).flatMap(p=>{try{if(fs.statSync(p).isDirectory())return fs.readdirSync(p).filter(n=>n.endsWith('.json')).sort().map(n=>path.join(p,n));}catch{}return [p];});
process.exitCode=main(paths);
